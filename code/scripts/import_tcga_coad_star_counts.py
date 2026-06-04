#!/usr/bin/env python3
import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path


DB_ARGS = [
    "docker",
    "exec",
    "-i",
    "bio-postgres",
    "psql",
    "-U",
    "bio",
    "-d",
    "bio",
    "-v",
    "ON_ERROR_STOP=1",
]
SCHEMA = "tcga_coad"
ROOT = Path("data/gdc_tcga_coad_star_counts")
GROUPS = [
    ("primary_tumor", ROOT / "manifests" / "primary_tumor_metadata.tsv", ROOT / "primary_tumor"),
    (
        "solid_tissue_normal",
        ROOT / "manifests" / "solid_tissue_normal_metadata.tsv",
        ROOT / "solid_tissue_normal",
    ),
]
NULL = r"\N"


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def run_sql(sql: str) -> None:
    subprocess.run(DB_ARGS, input=sql.encode("utf-8"), check=True)


def copy_rows(sql: str, rows) -> None:
    proc = subprocess.Popen(DB_ARGS + ["-c", sql], stdin=subprocess.PIPE)
    try:
        for row in rows:
            proc.stdin.write(row)
    finally:
        if proc.stdin:
            proc.stdin.close()
    if proc.wait() != 0:
        raise subprocess.CalledProcessError(proc.returncode, DB_ARGS)


def load_metadata() -> list[dict[str, str]]:
    rows = []
    for group, metadata_path, data_dir in GROUPS:
        if not metadata_path.exists():
            raise FileNotFoundError(metadata_path)
        if not data_dir.exists():
            raise FileNotFoundError(data_dir)
        with metadata_path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                row["source_group"] = group
                row["local_path"] = str(data_dir / row["file_name"])
                rows.append(row)
    return rows


def table_line(values: list[object]) -> bytes:
    cleaned = []
    for value in values:
        if value is None or value == "":
            cleaned.append(NULL)
        else:
            cleaned.append(str(value).replace("\\", "\\\\").replace("\t", " ").replace("\n", " "))
    return ("\t".join(cleaned) + "\n").encode("utf-8")


def create_schema() -> None:
    run_sql(
        f"""
DROP SCHEMA IF EXISTS {qident(SCHEMA)} CASCADE;
CREATE SCHEMA {qident(SCHEMA)};

CREATE TABLE {qident(SCHEMA)}.import_manifest (
  table_name text PRIMARY KEY,
  source text NOT NULL,
  loaded_at timestamptz NOT NULL DEFAULT now(),
  note text
);

CREATE TABLE {qident(SCHEMA)}.gdc_files (
  file_id uuid PRIMARY KEY,
  file_name text NOT NULL UNIQUE,
  file_size bigint NOT NULL,
  case_submitter_id text NOT NULL,
  sample_submitter_id text NOT NULL,
  sample_type text NOT NULL,
  source_group text NOT NULL,
  workflow_type text NOT NULL,
  local_path text NOT NULL
);

CREATE TABLE {qident(SCHEMA)}.genes (
  row_order integer PRIMARY KEY,
  gene_id text NOT NULL,
  gene_name text,
  gene_type text
);

CREATE TABLE {qident(SCHEMA)}.star_gene_counts (
  file_id uuid NOT NULL,
  row_order integer NOT NULL,
  gene_id text NOT NULL,
  unstranded bigint,
  stranded_first bigint,
  stranded_second bigint,
  tpm_unstranded double precision,
  fpkm_unstranded double precision,
  fpkm_uq_unstranded double precision
);
"""
    )


def metadata_rows(rows: list[dict[str, str]]):
    for row in rows:
        yield table_line(
            [
                row["file_id"],
                row["file_name"],
                row["file_size"],
                row["case_submitter_id"],
                row["sample_submitter_id"],
                row["sample_type"],
                row["source_group"],
                row["workflow_type"],
                row["local_path"],
            ]
        )


def iter_count_file(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        first = f.readline().rstrip("\n")
        gene_model = first.removeprefix("# gene-model: ").strip() if first.startswith("#") else ""
        reader = csv.DictReader(f, delimiter="\t")
        for row_order, row in enumerate(reader, 1):
            yield gene_model, row_order, row


def gene_rows(first_file: Path):
    for _, row_order, row in iter_count_file(first_file):
        yield table_line([row_order, row["gene_id"], row["gene_name"], row["gene_type"]])


def numeric(value: str) -> str | None:
    return value if value != "" else None


def count_rows(metadata: list[dict[str, str]], progress_every: float):
    total_files = len(metadata)
    started = time.time()
    last_progress = started
    rows_written = 0
    for idx, meta in enumerate(metadata, 1):
        path = Path(meta["local_path"])
        if not path.exists():
            raise FileNotFoundError(path)
        for _, row_order, row in iter_count_file(path):
            rows_written += 1
            yield table_line(
                [
                    meta["file_id"],
                    row_order,
                    row["gene_id"],
                    numeric(row["unstranded"]),
                    numeric(row["stranded_first"]),
                    numeric(row["stranded_second"]),
                    numeric(row["tpm_unstranded"]),
                    numeric(row["fpkm_unstranded"]),
                    numeric(row["fpkm_uq_unstranded"]),
                ]
            )
        now = time.time()
        if now - last_progress >= progress_every or idx == total_files:
            elapsed = max(now - started, 1)
            print(
                f"PROGRESS loaded_files={idx}/{total_files} rows_streamed={rows_written:,} "
                f"elapsed={elapsed/60:.1f} min",
                flush=True,
            )
            last_progress = now


def create_indexes_and_views() -> None:
    run_sql(
        f"""
CREATE INDEX star_gene_counts_file_id_idx ON {qident(SCHEMA)}.star_gene_counts(file_id);
CREATE INDEX star_gene_counts_gene_id_idx ON {qident(SCHEMA)}.star_gene_counts(gene_id);
CREATE INDEX gdc_files_sample_type_idx ON {qident(SCHEMA)}.gdc_files(sample_type);
CREATE INDEX gdc_files_case_submitter_id_idx ON {qident(SCHEMA)}.gdc_files(case_submitter_id);

CREATE VIEW {qident(SCHEMA)}.star_counts_with_metadata AS
SELECT
  f.file_id,
  f.case_submitter_id,
  f.sample_submitter_id,
  f.sample_type,
  f.source_group,
  c.row_order,
  c.gene_id,
  g.gene_name,
  g.gene_type,
  c.unstranded,
  c.stranded_first,
  c.stranded_second,
  c.tpm_unstranded,
  c.fpkm_unstranded,
  c.fpkm_uq_unstranded
FROM {qident(SCHEMA)}.star_gene_counts c
JOIN {qident(SCHEMA)}.gdc_files f ON f.file_id = c.file_id
LEFT JOIN {qident(SCHEMA)}.genes g ON g.row_order = c.row_order;

CREATE MATERIALIZED VIEW {qident(SCHEMA)}.protein_coding_tpm_matrix AS
SELECT
  c.file_id,
  f.case_submitter_id,
  f.sample_submitter_id,
  f.sample_type,
  jsonb_object_agg(g.gene_name, c.tpm_unstranded ORDER BY g.gene_name) AS tpm_by_gene
FROM {qident(SCHEMA)}.star_gene_counts c
JOIN {qident(SCHEMA)}.gdc_files f ON f.file_id = c.file_id
JOIN {qident(SCHEMA)}.genes g ON g.row_order = c.row_order
WHERE g.gene_type = 'protein_coding'
GROUP BY c.file_id, f.case_submitter_id, f.sample_submitter_id, f.sample_type;

CREATE UNIQUE INDEX protein_coding_tpm_matrix_file_id_idx
ON {qident(SCHEMA)}.protein_coding_tpm_matrix(file_id);

ANALYZE {qident(SCHEMA)}.gdc_files;
ANALYZE {qident(SCHEMA)}.genes;
ANALYZE {qident(SCHEMA)}.star_gene_counts;
ANALYZE {qident(SCHEMA)}.protein_coding_tpm_matrix;

INSERT INTO {qident(SCHEMA)}.import_manifest(table_name, source, note)
VALUES
  ('gdc_files', 'GDC API metadata manifests', 'TCGA-COAD STAR - Counts file metadata'),
  ('genes', 'first downloaded STAR counts file', 'Gene annotation and row order shared by GDC STAR counts files'),
  ('star_gene_counts', '522 downloaded STAR counts files', 'Long table: one row per file and GDC STAR counts row'),
  ('protein_coding_tpm_matrix', 'materialized view from star_gene_counts', 'One JSONB TPM vector per downloaded file for protein-coding genes');
"""
    )


def verify() -> None:
    run_sql(
        f"""
SELECT 'gdc_files' AS table_name, count(*)::bigint AS rows FROM {qident(SCHEMA)}.gdc_files
UNION ALL
SELECT 'genes', count(*)::bigint FROM {qident(SCHEMA)}.genes
UNION ALL
SELECT 'star_gene_counts', count(*)::bigint FROM {qident(SCHEMA)}.star_gene_counts
UNION ALL
SELECT 'protein_coding_tpm_matrix', count(*)::bigint FROM {qident(SCHEMA)}.protein_coding_tpm_matrix
ORDER BY table_name;

SELECT sample_type, count(*)::bigint AS files
FROM {qident(SCHEMA)}.gdc_files
GROUP BY sample_type
ORDER BY sample_type;
"""
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--progress-every", type=float, default=30)
    args = parser.parse_args()

    metadata = load_metadata()
    if not metadata:
        print("No metadata rows found.", file=sys.stderr)
        return 1

    first_file = Path(metadata[0]["local_path"])
    create_schema()
    copy_rows(
        f"COPY {qident(SCHEMA)}.gdc_files "
        "(file_id, file_name, file_size, case_submitter_id, sample_submitter_id, "
        "sample_type, source_group, workflow_type, local_path) "
        "FROM STDIN WITH (FORMAT text, DELIMITER E'\\t', NULL '\\N')",
        metadata_rows(metadata),
    )
    copy_rows(
        f"COPY {qident(SCHEMA)}.genes (row_order, gene_id, gene_name, gene_type) "
        "FROM STDIN WITH (FORMAT text, DELIMITER E'\\t', NULL '\\N')",
        gene_rows(first_file),
    )
    print(f"START loading {len(metadata)} STAR counts files into {SCHEMA}.star_gene_counts", flush=True)
    copy_rows(
        f"COPY {qident(SCHEMA)}.star_gene_counts "
        "(file_id, row_order, gene_id, unstranded, stranded_first, stranded_second, "
        "tpm_unstranded, fpkm_unstranded, fpkm_uq_unstranded) "
        "FROM STDIN WITH (FORMAT text, DELIMITER E'\\t', NULL '\\N')",
        count_rows(metadata, args.progress_every),
    )
    print("START creating indexes, views, and statistics", flush=True)
    create_indexes_and_views()
    verify()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

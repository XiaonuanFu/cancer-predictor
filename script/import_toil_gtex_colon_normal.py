#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "toil_gtex_colon_normal"
PHENOTYPE_FILE = DATA_DIR / "GTEX_phenotype.gz"
EXPRESSION_FILE = DATA_DIR / "gtex_RSEM_gene_tpm.gz"
PROBEMAP_FILE = DATA_DIR / "gencode.v23.annotation.gene.probemap"
SAMPLES_FILE = DATA_DIR / "gtex_colon_normal_samples.tsv"
SUBSET_MATRIX_FILE = DATA_DIR / "gtex_colon_normal_log2_tpm.tsv.gz"
SUMMARY_FILE = DATA_DIR / "gtex_colon_normal_summary.json"

SCHEMA = "toil_gtex_colon_normal"
TARGET_TISSUES = {"Colon - Sigmoid", "Colon - Transverse"}
NULL = r"\N"

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


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def table_line(values: list[object]) -> bytes:
    cleaned = []
    for value in values:
        if value is None or value == "":
            cleaned.append(NULL)
        else:
            cleaned.append(str(value).replace("\\", "\\\\").replace("\t", " ").replace("\n", " "))
    return ("\t".join(cleaned) + "\n").encode("utf-8")


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


def require_inputs() -> None:
    missing = [path for path in [PHENOTYPE_FILE, EXPRESSION_FILE, PROBEMAP_FILE] if not path.exists()]
    if missing:
        for path in missing:
            print(f"Missing input: {path}", file=sys.stderr)
        raise SystemExit(1)


def load_colon_samples() -> dict[str, dict[str, str]]:
    with gzip.open(PHENOTYPE_FILE, "rt", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    selected = {}
    for row in rows:
        tissue = row["body_site_detail (SMTSD)"]
        if tissue in TARGET_TISSUES:
            selected[row["Sample"]] = {
                "sample_id": row["Sample"],
                "body_site_detail": tissue,
                "primary_site": row["_primary_site"],
                "gender": row["_gender"],
                "patient": row["_patient"],
                "cohort": row["_cohort"],
            }
    return selected


def load_probemap() -> dict[str, dict[str, str]]:
    probemap = {}
    with PROBEMAP_FILE.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            probemap[row["id"]] = {
                "gene_symbol": row["gene"],
                "chrom": row["chrom"],
                "chrom_start": row["chromStart"],
                "chrom_end": row["chromEnd"],
                "strand": row["strand"],
            }
    return probemap


def get_expression_header() -> list[str]:
    with gzip.open(EXPRESSION_FILE, "rt", encoding="utf-8") as f:
        return f.readline().rstrip("\n").split("\t")


def write_selected_samples(samples: list[dict[str, str]]) -> None:
    fieldnames = ["sample_id", "body_site_detail", "primary_site", "gender", "patient", "cohort"]
    with SAMPLES_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(samples)


def create_subset_matrix(
    selected_samples: list[dict[str, str]],
    sample_column_indexes: list[int],
    probemap: dict[str, dict[str, str]],
    progress_every: float,
) -> dict[str, int]:
    started = time.time()
    last_progress = started
    genes = 0

    with gzip.open(EXPRESSION_FILE, "rt", encoding="utf-8", newline="") as src:
        header = src.readline().rstrip("\n").split("\t")
        sample_ids = [sample["sample_id"] for sample in selected_samples]
        output_header = ["gene_id", "gene_symbol", "chrom", "chrom_start", "chrom_end", "strand"] + sample_ids

        with gzip.open(SUBSET_MATRIX_FILE, "wt", encoding="utf-8", newline="") as out:
            out.write("\t".join(output_header) + "\n")
            for line in src:
                parts = line.rstrip("\n").split("\t")
                gene_id = parts[0]
                gene = probemap.get(gene_id, {})
                values = [parts[i] for i in sample_column_indexes]
                out.write(
                    "\t".join(
                        [
                            gene_id,
                            gene.get("gene_symbol", ""),
                            gene.get("chrom", ""),
                            gene.get("chrom_start", ""),
                            gene.get("chrom_end", ""),
                            gene.get("strand", ""),
                            *values,
                        ]
                    )
                    + "\n"
                )
                genes += 1
                now = time.time()
                if now - last_progress >= progress_every:
                    elapsed = max(now - started, 1)
                    print(f"PROGRESS subset genes={genes:,} elapsed={elapsed/60:.1f} min", flush=True)
                    last_progress = now

    return {"genes": genes, "samples": len(selected_samples), "expression_values": genes * len(selected_samples)}


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

CREATE TABLE {qident(SCHEMA)}.samples (
  sample_id text PRIMARY KEY,
  body_site_detail text NOT NULL,
  primary_site text NOT NULL,
  gender text,
  patient text,
  cohort text NOT NULL
);

CREATE TABLE {qident(SCHEMA)}.genes (
  gene_id text PRIMARY KEY,
  gene_symbol text,
  chrom text,
  chrom_start integer,
  chrom_end integer,
  strand text
);

CREATE TABLE {qident(SCHEMA)}.expression_log2_tpm (
  sample_id text NOT NULL,
  gene_id text NOT NULL,
  log2_tpm double precision
);
"""
    )


def sample_rows(samples: list[dict[str, str]]):
    for sample in samples:
        yield table_line(
            [
                sample["sample_id"],
                sample["body_site_detail"],
                sample["primary_site"],
                sample["gender"],
                sample["patient"],
                sample["cohort"],
            ]
        )


def gene_rows(probemap: dict[str, dict[str, str]], matrix_gene_ids: list[str]):
    for gene_id in matrix_gene_ids:
        gene = probemap.get(gene_id, {})
        yield table_line(
            [
                gene_id,
                gene.get("gene_symbol"),
                gene.get("chrom"),
                gene.get("chrom_start"),
                gene.get("chrom_end"),
                gene.get("strand"),
            ]
        )


def read_matrix_gene_ids() -> list[str]:
    gene_ids = []
    with gzip.open(EXPRESSION_FILE, "rt", encoding="utf-8") as f:
        next(f)
        for line in f:
            gene_ids.append(line.split("\t", 1)[0])
    return gene_ids


def expression_rows(sample_ids: list[str], sample_column_indexes: list[int], progress_every: float):
    started = time.time()
    last_progress = started
    genes = 0
    rows = 0
    with gzip.open(EXPRESSION_FILE, "rt", encoding="utf-8", newline="") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split("\t")
            gene_id = parts[0]
            for sample_id, column_index in zip(sample_ids, sample_column_indexes):
                rows += 1
                yield table_line([sample_id, gene_id, parts[column_index]])
            genes += 1
            now = time.time()
            if now - last_progress >= progress_every:
                elapsed = max(now - started, 1)
                print(
                    f"PROGRESS import genes={genes:,} expression_rows={rows:,} elapsed={elapsed/60:.1f} min",
                    flush=True,
                )
                last_progress = now


def create_indexes_and_views() -> None:
    run_sql(
        f"""
CREATE INDEX expression_log2_tpm_sample_id_idx ON {qident(SCHEMA)}.expression_log2_tpm(sample_id);
CREATE INDEX expression_log2_tpm_gene_id_idx ON {qident(SCHEMA)}.expression_log2_tpm(gene_id);
CREATE INDEX samples_body_site_detail_idx ON {qident(SCHEMA)}.samples(body_site_detail);
CREATE INDEX genes_gene_symbol_idx ON {qident(SCHEMA)}.genes(gene_symbol);

CREATE VIEW {qident(SCHEMA)}.expression_with_metadata AS
SELECT
  s.sample_id,
  s.body_site_detail,
  s.primary_site,
  s.gender,
  s.patient,
  s.cohort,
  e.gene_id,
  g.gene_symbol,
  g.chrom,
  g.chrom_start,
  g.chrom_end,
  g.strand,
  e.log2_tpm
FROM {qident(SCHEMA)}.expression_log2_tpm e
JOIN {qident(SCHEMA)}.samples s ON s.sample_id = e.sample_id
LEFT JOIN {qident(SCHEMA)}.genes g ON g.gene_id = e.gene_id;

ANALYZE {qident(SCHEMA)}.samples;
ANALYZE {qident(SCHEMA)}.genes;
ANALYZE {qident(SCHEMA)}.expression_log2_tpm;

INSERT INTO {qident(SCHEMA)}.import_manifest(table_name, source, note)
VALUES
  ('samples', 'UCSC Xena Toil GTEX_phenotype.gz', 'GTEx normal colon samples: Colon - Sigmoid and Colon - Transverse'),
  ('genes', 'UCSC Xena Toil gencode.v23.annotation.gene.probemap', 'GENCODE v23 gene annotation used by the Toil expression matrix'),
  ('expression_log2_tpm', 'UCSC Xena Toil gtex_RSEM_gene_tpm.gz', 'RSEM gene TPM expression on the UCSC Xena log2 scale; zero TPM appears near -9.9658');
"""
    )


def verify() -> None:
    run_sql(
        f"""
SELECT 'samples' AS table_name, count(*)::bigint AS rows FROM {qident(SCHEMA)}.samples
UNION ALL
SELECT 'genes', count(*)::bigint FROM {qident(SCHEMA)}.genes
UNION ALL
SELECT 'expression_log2_tpm', count(*)::bigint FROM {qident(SCHEMA)}.expression_log2_tpm
ORDER BY table_name;

SELECT body_site_detail, count(*)::bigint AS samples
FROM {qident(SCHEMA)}.samples
GROUP BY body_site_detail
ORDER BY body_site_detail;
"""
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-subset", action="store_true", help="Do not rewrite the local subset matrix file.")
    parser.add_argument("--skip-import", action="store_true", help="Create local files only; do not load PostgreSQL.")
    parser.add_argument("--progress-every", type=float, default=30)
    args = parser.parse_args()

    require_inputs()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    colon_samples = load_colon_samples()
    probemap = load_probemap()
    header = get_expression_header()
    column_by_sample = {sample_id: i for i, sample_id in enumerate(header)}
    selected_samples = [colon_samples[sample_id] for sample_id in header[1:] if sample_id in colon_samples]
    sample_ids = [sample["sample_id"] for sample in selected_samples]
    sample_column_indexes = [column_by_sample[sample_id] for sample_id in sample_ids]

    if not selected_samples:
        print("No colon samples from phenotype were present in the expression matrix.", file=sys.stderr)
        return 1

    tissue_counts = Counter(sample["body_site_detail"] for sample in selected_samples)
    write_selected_samples(selected_samples)

    if args.skip_subset and SUBSET_MATRIX_FILE.exists():
        matrix_gene_ids = read_matrix_gene_ids()
        subset_stats = {
            "genes": len(matrix_gene_ids),
            "samples": len(selected_samples),
            "expression_values": len(matrix_gene_ids) * len(selected_samples),
        }
    else:
        subset_stats = create_subset_matrix(selected_samples, sample_column_indexes, probemap, args.progress_every)
        matrix_gene_ids = read_matrix_gene_ids()

    summary = {
        "source": "UCSC Xena Toil GTEx RSEM gene TPM",
        "source_urls": {
            "phenotype": "https://toil.xenahubs.net/download/GTEX_phenotype.gz",
            "expression": "https://toil.xenahubs.net/download/gtex_RSEM_gene_tpm.gz",
            "probemap": "https://toil.xenahubs.net/download/probeMap/gencode.v23.annotation.gene.probemap",
        },
        "selected_tissues": sorted(TARGET_TISSUES),
        "sample_counts": dict(sorted(tissue_counts.items())),
        "total_samples": len(selected_samples),
        "genes": subset_stats["genes"],
        "expression_values": subset_stats["expression_values"],
        "local_files": {
            "phenotype": str(PHENOTYPE_FILE),
            "expression": str(EXPRESSION_FILE),
            "probemap": str(PROBEMAP_FILE),
            "samples": str(SAMPLES_FILE),
            "subset_matrix": str(SUBSET_MATRIX_FILE),
        },
        "database_schema": None if args.skip_import else SCHEMA,
        "expression_scale_note": "Values are stored as log2 TPM on the UCSC Xena Toil scale; zero TPM appears near -9.9658.",
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"Selected samples={len(selected_samples)} genes={subset_stats['genes']:,} "
        f"expression_values={subset_stats['expression_values']:,}",
        flush=True,
    )
    print(f"Tissue counts: {dict(sorted(tissue_counts.items()))}", flush=True)

    if args.skip_import:
        return 0

    create_schema()
    copy_rows(
        f"COPY {qident(SCHEMA)}.samples "
        "(sample_id, body_site_detail, primary_site, gender, patient, cohort) "
        "FROM STDIN WITH (FORMAT text, DELIMITER E'\\t', NULL '\\N')",
        sample_rows(selected_samples),
    )
    copy_rows(
        f"COPY {qident(SCHEMA)}.genes "
        "(gene_id, gene_symbol, chrom, chrom_start, chrom_end, strand) "
        "FROM STDIN WITH (FORMAT text, DELIMITER E'\\t', NULL '\\N')",
        gene_rows(probemap, matrix_gene_ids),
    )
    print(f"START loading expression values into {SCHEMA}.expression_log2_tpm", flush=True)
    copy_rows(
        f"COPY {qident(SCHEMA)}.expression_log2_tpm "
        "(sample_id, gene_id, log2_tpm) "
        "FROM STDIN WITH (FORMAT text, DELIMITER E'\\t', NULL '\\N')",
        expression_rows(sample_ids, sample_column_indexes, args.progress_every),
    )
    print("START creating indexes, views, and statistics", flush=True)
    create_indexes_and_views()
    verify()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

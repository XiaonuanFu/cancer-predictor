from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text

from . import config


@dataclass(frozen=True)
class PreparedData:
    features: pd.DataFrame
    labels: pd.DataFrame
    shared_genes: list[str]
    summary: dict


def sqlalchemy_engine():
    return create_engine(config.db_url())


def psycopg_connection():
    return psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )


def read_coad_tumor_samples() -> pd.DataFrame:
    query = """
    WITH coad_patients AS (
      SELECT bcr_patient_barcode
      FROM bio_tcga.tcga_cdr_tcga_cdr
      WHERE type = 'COAD'
    )
    SELECT
      s.sample_index,
      s.sample_id,
      substring(s.sample_id from 1 for 12) AS case_submitter_id,
      substring(s.sample_id from 14 for 2) AS sample_type_code
    FROM bio_tcga.matrix_rnaseq_gene_expression_samples s
    JOIN coad_patients c
      ON substring(s.sample_id from 1 for 12) = c.bcr_patient_barcode
    WHERE substring(s.sample_id from 14 for 2) = '01'
    ORDER BY s.sample_index;
    """
    with sqlalchemy_engine().connect() as conn:
        samples = pd.read_sql_query(text(query), conn)
    samples["source_schema"] = "bio_tcga"
    samples["source_table"] = "matrix_rnaseq_gene_expression"
    samples["sample_type"] = "Primary Tumor"
    samples["sample_submitter_id"] = samples["sample_id"]
    samples["label"] = "tumor"
    return samples


def read_normal_metadata() -> pd.DataFrame:
    query = """
    SELECT DISTINCT
      f.file_id::text AS file_id,
      f.case_submitter_id,
      f.sample_submitter_id,
      f.sample_type
    FROM tcga_coad.gdc_files f
    WHERE f.sample_type = 'Solid Tissue Normal'
    ORDER BY f.sample_submitter_id;
    """
    with sqlalchemy_engine().connect() as conn:
        samples = pd.read_sql_query(text(query), conn)
    samples["sample_id"] = samples["sample_submitter_id"]
    samples["source_schema"] = "tcga_coad"
    samples["source_table"] = "star_counts_with_metadata"
    samples["label"] = "normal"
    return samples


def read_normal_matrix() -> pd.DataFrame:
    query = """
    SELECT
      sample_submitter_id AS sample_id,
      gene_name,
      tpm_unstranded
    FROM tcga_coad.star_counts_with_metadata
    WHERE sample_type = 'Solid Tissue Normal'
      AND gene_type = 'protein_coding'
      AND gene_name IS NOT NULL
      AND tpm_unstranded IS NOT NULL;
    """
    with sqlalchemy_engine().connect() as conn:
        long_df = pd.read_sql_query(text(query), conn)
    matrix = long_df.pivot_table(
        index="sample_id",
        columns="gene_name",
        values="tpm_unstranded",
        aggfunc="mean",
    )
    matrix.index.name = "sample_id"
    return matrix.sort_index(axis=1)


def read_tumor_gene_symbols() -> pd.DataFrame:
    query = """
    SELECT
      feature_id,
      split_part(feature_id, '|', 1) AS gene_symbol
    FROM bio_tcga.matrix_rnaseq_gene_expression
    WHERE split_part(feature_id, '|', 1) <> '?';
    """
    with sqlalchemy_engine().connect() as conn:
        return pd.read_sql_query(text(query), conn)


def parse_expression_values(values_text: str, zero_based_positions: np.ndarray) -> np.ndarray:
    try:
        values = np.fromstring(values_text, sep=" ", dtype=np.float64)
    except ValueError:
        parsed = []
        for token in values_text.split():
            try:
                parsed.append(float(token))
            except ValueError:
                parsed.append(np.nan)
        values = np.asarray(parsed, dtype=np.float64)
    if zero_based_positions.size and values.size <= int(zero_based_positions.max()):
        raise ValueError("Expression vector is shorter than the requested sample positions.")
    return values[zero_based_positions]


def iter_tumor_feature_rows(feature_ids: Iterable[str], fetch_size: int = 200):
    feature_ids = list(feature_ids)
    with psycopg_connection() as conn:
        with conn.cursor(name="coad_tumor_expression_cursor") as cursor:
            cursor.itersize = fetch_size
            cursor.execute(
                """
                SELECT feature_id, split_part(feature_id, '|', 1) AS gene_symbol, values_text
                FROM bio_tcga.matrix_rnaseq_gene_expression
                WHERE feature_id = ANY(%s)
                ORDER BY feature_id;
                """,
                (feature_ids,),
            )
            while True:
                rows = cursor.fetchmany(fetch_size)
                if not rows:
                    break
                for row in rows:
                    yield row


def build_tumor_matrix(tumor_samples: pd.DataFrame, tumor_features: pd.DataFrame) -> pd.DataFrame:
    sample_positions = tumor_samples["sample_index"].to_numpy(dtype=np.int64) - 1
    sample_ids = tumor_samples["sample_id"].tolist()
    columns = []
    data = []
    feature_ids = tumor_features["feature_id"].tolist()

    for feature_id, gene_symbol, values_text in iter_tumor_feature_rows(feature_ids):
        columns.append(gene_symbol)
        data.append(parse_expression_values(values_text, sample_positions))

    matrix = pd.DataFrame(np.asarray(data, dtype=np.float64).T, index=sample_ids, columns=columns)
    matrix.index.name = "sample_id"
    if matrix.columns.duplicated().any():
        matrix = matrix.T.groupby(level=0).mean().T
    return matrix.sort_index(axis=1)


def build_prepared_data() -> PreparedData:
    config.ensure_dirs()

    tumor_samples = read_coad_tumor_samples()
    normal_samples = read_normal_metadata()
    normal_matrix = read_normal_matrix()
    tumor_symbols = read_tumor_gene_symbols()

    normal_genes = set(normal_matrix.columns)
    tumor_symbols = tumor_symbols[tumor_symbols["gene_symbol"].isin(normal_genes)].copy()
    shared_genes = sorted(set(tumor_symbols["gene_symbol"]) & normal_genes)
    tumor_features = tumor_symbols[tumor_symbols["gene_symbol"].isin(shared_genes)].copy()

    tumor_matrix = build_tumor_matrix(tumor_samples, tumor_features)
    if tumor_matrix.columns.duplicated().any():
        tumor_matrix = tumor_matrix.T.groupby(level=0).mean().T

    shared_genes = sorted(set(tumor_matrix.columns) & set(normal_matrix.columns))
    tumor_matrix = tumor_matrix.loc[:, shared_genes]
    normal_matrix = normal_matrix.loc[:, shared_genes]

    features = pd.concat([tumor_matrix, normal_matrix], axis=0)
    labels = pd.concat(
        [
            tumor_samples.set_index("sample_id"),
            normal_samples.set_index("sample_id"),
        ],
        axis=0,
        sort=False,
    ).loc[features.index]
    labels.index.name = "sample_id"
    labels = labels.reset_index()

    summary = {
        "tumor_samples": int((labels["label"] == "tumor").sum()),
        "normal_samples": int((labels["label"] == "normal").sum()),
        "shared_genes": len(shared_genes),
        "tumor_source": "bio_tcga.matrix_rnaseq_gene_expression",
        "normal_source": "tcga_coad.star_counts_with_metadata.tpm_unstranded",
        "notes": [
            "Tumor and normal expression data come from different schemas/pipelines.",
            "Raw database tables and source files are not modified.",
            "Only shared gene symbols are used.",
        ],
    }

    features.to_parquet(config.RAW_FEATURES_FILE)
    labels.to_csv(config.LABELS_FILE, index=False)
    config.SELECTED_GENES_FILE.write_text("\n".join(shared_genes) + "\n", encoding="utf-8")
    config.DATA_SUMMARY_FILE.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    return PreparedData(features=features, labels=labels, shared_genes=shared_genes, summary=summary)


def load_prepared_features() -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_path = config.RAW_FEATURES_FILE if config.RAW_FEATURES_FILE.exists() else config.FEATURES_FILE
    features = pd.read_parquet(feature_path)
    labels = pd.read_csv(config.LABELS_FILE)
    labels = labels.set_index("sample_id").loc[features.index].reset_index()
    return features, labels

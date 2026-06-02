from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import config


def to_markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "(none)"
    columns = list(df.columns)
    rows = ["| " + " | ".join(columns) + " |"]
    rows.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for _, row in df.iterrows():
        values = [str(row[col]).replace("|", "\\|") for col in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def extract_important_genes(trained_models, feature_names: list[str], top_n: int = 30) -> pd.DataFrame:
    records = []
    for trained in trained_models:
        model = trained.pipeline.named_steps["model"]
        if hasattr(model, "coef_"):
            scores = np.ravel(model.coef_)
            order = np.argsort(np.abs(scores))[::-1][:top_n]
            for rank, idx in enumerate(order, 1):
                score = float(scores[idx])
                records.append(
                    {
                        "model": trained.name,
                        "rank": rank,
                        "gene_symbol": feature_names[idx],
                        "importance_score": score,
                        "direction": "higher_tumor_score" if score > 0 else "higher_normal_score",
                        "short_explanation": "Candidate predictive gene; requires follow-up literature review.",
                    }
                )
        elif hasattr(model, "feature_importances_"):
            scores = np.ravel(model.feature_importances_)
            order = np.argsort(scores)[::-1][:top_n]
            for rank, idx in enumerate(order, 1):
                records.append(
                    {
                        "model": trained.name,
                        "rank": rank,
                        "gene_symbol": feature_names[idx],
                        "importance_score": float(scores[idx]),
                        "direction": "tree_importance",
                        "short_explanation": "Candidate predictive gene; requires follow-up literature review.",
                    }
                )
    important = pd.DataFrame(records)
    important.to_csv(config.IMPORTANT_GENES_FILE, index=False)
    return important


def write_model_report(metrics: pd.DataFrame, important: pd.DataFrame) -> None:
    summary = {}
    if config.DATA_SUMMARY_FILE.exists():
        summary = json.loads(config.DATA_SUMMARY_FILE.read_text(encoding="utf-8"))
    model_gene_count = "unknown"
    if config.SELECTED_GENES_FILE.exists():
        model_gene_count = len(
            [line for line in config.SELECTED_GENES_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
        )

    top_genes = (
        important.sort_values(["model", "rank"])
        .groupby("model")
        .head(10)[["model", "rank", "gene_symbol", "importance_score", "direction"]]
    )
    metrics_md = to_markdown_table(metrics.drop(columns=["confusion_matrix"], errors="ignore"))
    genes_md = to_markdown_table(top_genes)

    report = f"""# COAD Tumor vs Normal RNA Expression Model Report

## Summary

This is an exploratory, research-only COAD tumor vs normal classifier.

This report uses RNA expression to build a COAD colon cancer tumor/normal binary classifier. Tumor samples come from `bio_tcga`, while normal samples come from `tcga_coad`; the two sources may have different processing pipelines, so results must not be interpreted as a clinical diagnostic model.

## Data

- Tumor samples: {summary.get("tumor_samples", "unknown")}
- Normal samples: {summary.get("normal_samples", "unknown")}
- Shared protein-coding genes before low-variance filtering: {summary.get("shared_genes", "unknown")}
- Model genes after low-variance filtering: {model_gene_count}
- Tumor source: {summary.get("tumor_source", "unknown")}
- Normal source: {summary.get("normal_source", "unknown")}
- Preprocessing: `log2(x + 1)`, low-variance filtering, median imputation inside each model Pipeline, class imbalance handled with `class_weight='balanced'`.

## Metrics

{metrics_md}

## Top Important Genes

{genes_md}

## Caveats

- This is research-only and not for clinical diagnosis.
- Tumor and normal data come from different schemas/pipelines.
- Important genes are predictive features, not proven causal cancer drivers.
- Further literature review and external validation are required.
"""
    config.MODEL_REPORT_FILE.write_text(report, encoding="utf-8")

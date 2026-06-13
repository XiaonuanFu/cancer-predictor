#!/usr/bin/env python3
from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import nbformat as nbf
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_recall_fscore_support,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import LinearSVC


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = PROJECT_ROOT / "code" / "coad-predictor-model"
DATA_ROOT = PROJECT_ROOT / "data" / "gdc_tcga_coad_star_counts"
REPORTS_DIR = MODEL_ROOT / "reports"
MODELS_DIR = MODEL_ROOT / "models"
JUPYTER_REPORTS_DIR = PROJECT_ROOT / "docker_storage" / "jupyter" / "coad-predictor-model" / "reports"
JUPYTER_MODELS_DIR = PROJECT_ROOT / "docker_storage" / "jupyter" / "coad-predictor-model" / "models"

PREFIX = "tcga_adjacent_normal"
RANDOM_STATE = 42
POSITIVE_LABEL = "tumor"
MODEL_ORDER = ["logistic_regression", "random_forest", "linear_svm"]


@dataclass(frozen=True)
class ModelResult:
    name: str
    pipeline: Pipeline
    path: Path


def model_definitions() -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=5000,
                        random_state=RANDOM_STATE,
                        solver="liblinear",
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=200,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "linear_svm": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LinearSVC(
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        max_iter=10000,
                        dual=True,
                    ),
                ),
            ]
        ),
    }


def load_metadata() -> pd.DataFrame:
    rows = []
    for group, label, manifest_name in [
        ("primary_tumor", "tumor", "primary_tumor_metadata.tsv"),
        ("solid_tissue_normal", "normal", "solid_tissue_normal_metadata.tsv"),
    ]:
        manifest = DATA_ROOT / "manifests" / manifest_name
        metadata = pd.read_csv(manifest, sep="\t")
        metadata["label"] = label
        metadata["source_group"] = group
        metadata["local_path"] = metadata["file_name"].map(lambda name: str(DATA_ROOT / group / name))
        rows.append(metadata)
    metadata = pd.concat(rows, ignore_index=True)
    metadata = metadata[metadata["local_path"].map(lambda path: Path(path).exists())].copy()
    return metadata


def read_expression_file(path: Path) -> pd.Series:
    df = pd.read_csv(
        path,
        sep="\t",
        comment="#",
        usecols=["gene_name", "gene_type", "tpm_unstranded"],
        dtype={"gene_name": "string", "gene_type": "string", "tpm_unstranded": "float64"},
    )
    df = df[(df["gene_type"] == "protein_coding") & df["gene_name"].notna() & df["tpm_unstranded"].notna()]
    series = df.groupby("gene_name", sort=False)["tpm_unstranded"].mean()
    return series


def build_feature_matrix(metadata: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    sample_ids = []
    total = len(metadata)
    for idx, row in enumerate(metadata.itertuples(index=False), 1):
        rows.append(read_expression_file(Path(row.local_path)))
        sample_ids.append(row.sample_submitter_id)
        if idx % 50 == 0 or idx == total:
            print(f"Loaded {idx}/{total} TCGA STAR count files", flush=True)

    features = pd.DataFrame(rows, index=sample_ids)
    features.index.name = "sample_id"
    if features.index.duplicated().any():
        features = features.groupby(level=0).mean()

    labels = metadata.drop_duplicates("sample_submitter_id").set_index("sample_submitter_id")
    labels.index.name = "sample_id"
    labels = labels.loc[features.index].reset_index()
    return features.sort_index(axis=1), labels


def prepare_model_inputs(features: pd.DataFrame, labels: pd.DataFrame):
    transformed = np.log2(features.clip(lower=0) + 1.0)
    variances = transformed.var(axis=0, skipna=True)
    transformed = transformed.loc[:, variances[variances > 1e-8].index]

    encoder = LabelEncoder()
    y = encoder.fit_transform(labels["label"])
    groups = labels["case_submitter_id"].fillna(labels["sample_id"]).astype(str).to_numpy()
    idx = np.arange(len(labels))

    try:
        splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
        train_idx, test_idx = next(splitter.split(idx, y, groups))
    except Exception:
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE)
        train_idx, test_idx = next(splitter.split(idx, y, groups))
    return transformed, y, encoder, train_idx, test_idx


def model_scores(pipeline: Pipeline, x_test: pd.DataFrame, tumor_index: int):
    if hasattr(pipeline, "predict_proba"):
        return pipeline.predict_proba(x_test)[:, tumor_index]
    if hasattr(pipeline, "decision_function"):
        return pipeline.decision_function(x_test)
    return pipeline.predict(x_test)


def evaluate_models(trained, model_features, y, encoder, test_idx) -> tuple[pd.DataFrame, dict]:
    x_test = model_features.iloc[test_idx]
    y_test = y[test_idx]
    target_names = list(encoder.classes_)
    tumor_index = target_names.index(POSITIVE_LABEL)
    y_binary = (y_test == tumor_index).astype(int)
    records = []
    curves = {}

    for result in trained:
        y_pred = result.pipeline.predict(x_test)
        scores = model_scores(result.pipeline, x_test, tumor_index)
        precision, recall, f1_by_class, support = precision_recall_fscore_support(
            y_test,
            y_pred,
            labels=list(range(len(target_names))),
            zero_division=0,
        )
        cm = confusion_matrix(y_test, y_pred, labels=list(range(len(target_names))))
        record = {
            "model": result.name,
            "accuracy": accuracy_score(y_test, y_pred),
            "balanced_accuracy": balanced_accuracy_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred, pos_label=tumor_index, zero_division=0),
            "roc_auc": roc_auc_score(y_binary, scores),
            "pr_auc": average_precision_score(y_binary, scores),
            "confusion_matrix": cm.tolist(),
        }
        for i, label in enumerate(target_names):
            record[f"{label}_precision"] = precision[i]
            record[f"{label}_recall"] = recall[i]
            record[f"{label}_f1"] = f1_by_class[i]
            record[f"{label}_support"] = int(support[i])
        records.append(record)

        fpr, tpr, _ = roc_curve(y_binary, scores)
        pr_precision, pr_recall, _ = precision_recall_curve(y_binary, scores)
        curves[result.name] = {
            "fpr": fpr,
            "tpr": tpr,
            "precision": pr_precision,
            "recall": pr_recall,
            "cm": cm,
        }

    metrics = pd.DataFrame(records)
    metrics["model"] = pd.Categorical(metrics["model"], categories=MODEL_ORDER, ordered=True)
    return metrics.sort_values("model").reset_index(drop=True), curves


def extract_important_genes(trained, feature_names: list[str], top_n: int = 30) -> pd.DataFrame:
    records = []
    for result in trained:
        model = result.pipeline.named_steps["model"]
        if hasattr(model, "coef_"):
            scores = np.ravel(model.coef_)
            order = np.argsort(np.abs(scores))[::-1][:top_n]
            for rank, idx in enumerate(order, 1):
                score = float(scores[idx])
                records.append(
                    {
                        "model": result.name,
                        "rank": rank,
                        "gene_symbol": feature_names[idx],
                        "importance_score": score,
                        "direction": "higher_tumor_score" if score > 0 else "higher_normal_score",
                    }
                )
        elif hasattr(model, "feature_importances_"):
            scores = np.ravel(model.feature_importances_)
            order = np.argsort(scores)[::-1][:top_n]
            for rank, idx in enumerate(order, 1):
                records.append(
                    {
                        "model": result.name,
                        "rank": rank,
                        "gene_symbol": feature_names[idx],
                        "importance_score": float(scores[idx]),
                        "direction": "tree_importance",
                    }
                )
    important = pd.DataFrame(records)
    important["model"] = pd.Categorical(important["model"], categories=MODEL_ORDER, ordered=True)
    return important.sort_values(["model", "rank"]).reset_index(drop=True)


def svg_text(x, y, text, size=12, anchor="start", weight="normal"):
    safe = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<text x="{x}" y="{y}" font-size="{size}" font-family="Arial" text-anchor="{anchor}" font-weight="{weight}">{safe}</text>'


def write_metric_svg(metrics: pd.DataFrame, path: Path) -> None:
    plot_metrics = ["accuracy", "balanced_accuracy", "normal_recall", "tumor_recall", "roc_auc", "pr_auc"]
    colors = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2"]
    width, height = 980, 420
    left, top, chart_h = 80, 70, 260
    group_w = 260
    bar_w = 28
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(svg_text(width / 2, 30, "TCGA-only model metric comparison", 18, "middle", "bold"))
    for tick in np.linspace(0, 1, 6):
        y = top + chart_h - tick * chart_h
        parts.append(f'<line x1="{left}" y1="{y}" x2="{width-40}" y2="{y}" stroke="#ddd"/>')
        parts.append(svg_text(left - 10, y + 4, f"{tick:.1f}", 11, "end"))
    for model_i, (_, row) in enumerate(metrics.iterrows()):
        x0 = left + model_i * group_w + 20
        for metric_i, metric in enumerate(plot_metrics):
            score = float(row[metric])
            h = score * chart_h
            x = x0 + metric_i * (bar_w + 4)
            y = top + chart_h - h
            parts.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" fill="{colors[metric_i]}"/>')
        parts.append(svg_text(x0 + 92, top + chart_h + 32, row["model"], 12, "middle"))
    for i, metric in enumerate(plot_metrics):
        lx = left + i * 145
        ly = height - 45
        parts.append(f'<rect x="{lx}" y="{ly-12}" width="14" height="14" fill="{colors[i]}"/>')
        parts.append(svg_text(lx + 20, ly, metric, 11))
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_confusion_svg(metrics: pd.DataFrame, target_names: list[str], path: Path) -> None:
    width, height = 980, 330
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(svg_text(width / 2, 30, "Confusion matrices", 18, "middle", "bold"))
    for model_i, (_, row) in enumerate(metrics.iterrows()):
        cm = np.array(row["confusion_matrix"])
        max_v = max(cm.max(), 1)
        x0 = 70 + model_i * 310
        y0 = 80
        parts.append(svg_text(x0 + 95, 58, row["model"], 13, "middle", "bold"))
        for i in range(2):
            for j in range(2):
                v = int(cm[i, j])
                intensity = int(245 - 155 * (v / max_v))
                fill = f"rgb({intensity},{intensity+5},255)"
                x = x0 + j * 90
                y = y0 + i * 70
                parts.append(f'<rect x="{x}" y="{y}" width="90" height="70" fill="{fill}" stroke="#444"/>')
                parts.append(svg_text(x + 45, y + 42, v, 18, "middle", "bold"))
        parts.append(svg_text(x0 + 45, y0 + 170, target_names[0], 11, "middle"))
        parts.append(svg_text(x0 + 135, y0 + 170, target_names[1], 11, "middle"))
        parts.append(svg_text(x0 - 10, y0 + 43, target_names[0], 11, "end"))
        parts.append(svg_text(x0 - 10, y0 + 113, target_names[1], 11, "end"))
        parts.append(svg_text(x0 + 90, y0 + 200, "Predicted", 11, "middle"))
        parts.append(svg_text(x0 - 55, y0 + 80, "True", 11, "middle"))
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def points(values_x, values_y, x0, y0, w, h):
    return " ".join(f"{x0 + float(x)*w:.1f},{y0 + h - float(y)*h:.1f}" for x, y in zip(values_x, values_y))


def write_curve_svg(curves: dict, path: Path) -> None:
    width, height = 980, 420
    colors = {"logistic_regression": "#4C78A8", "random_forest": "#F58518", "linear_svm": "#54A24B"}
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    for panel, title, xkey, ykey in [(0, "ROC Curve", "fpr", "tpr"), (1, "Precision-Recall Curve", "recall", "precision")]:
        x0 = 70 + panel * 470
        y0 = 70
        w, h = 360, 260
        parts.append(svg_text(x0 + w / 2, 35, title, 17, "middle", "bold"))
        parts.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="none" stroke="#333"/>')
        for tick in np.linspace(0, 1, 6):
            x = x0 + tick * w
            y = y0 + h - tick * h
            parts.append(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y0+h}" stroke="#eee"/>')
            parts.append(f'<line x1="{x0}" y1="{y}" x2="{x0+w}" y2="{y}" stroke="#eee"/>')
        for name, curve in curves.items():
            parts.append(
                f'<polyline fill="none" stroke="{colors.get(name, "#333")}" stroke-width="2" '
                f'points="{points(curve[xkey], curve[ykey], x0, y0, w, h)}"/>'
            )
        parts.append(svg_text(x0 + w / 2, y0 + h + 40, "Recall" if panel else "False Positive Rate", 12, "middle"))
        parts.append(svg_text(x0 - 42, y0 + h / 2, "Precision" if panel else "True Positive Rate", 12, "middle"))
    for i, name in enumerate(MODEL_ORDER):
        x = 360 + i * 180
        parts.append(f'<rect x="{x}" y="{height-35}" width="14" height="14" fill="{colors[name]}"/>')
        parts.append(svg_text(x + 20, height - 23, name, 11))
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_important_svg(important: pd.DataFrame, path: Path) -> None:
    width, height = 980, 760
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(svg_text(width / 2, 30, "Top important genes by model", 18, "middle", "bold"))
    y = 70
    for model_name in MODEL_ORDER:
        subset = important[important["model"] == model_name].head(10).copy()
        max_abs = max(float(subset["importance_score"].abs().max()), 1e-12)
        parts.append(svg_text(40, y, model_name, 14, "start", "bold"))
        y += 22
        for _, row in subset.iterrows():
            score = float(row["importance_score"])
            bar_w = abs(score) / max_abs * 280
            x0 = 250
            color = "#4C78A8" if "normal" in str(row["direction"]) else "#F58518"
            if score >= 0:
                parts.append(f'<rect x="{x0}" y="{y-12}" width="{bar_w}" height="14" fill="{color}"/>')
            else:
                parts.append(f'<rect x="{x0-bar_w}" y="{y-12}" width="{bar_w}" height="14" fill="{color}"/>')
            parts.append(f'<line x1="{x0}" y1="{y-16}" x2="{x0}" y2="{y+4}" stroke="#333"/>')
            parts.append(svg_text(40, y, row["gene_symbol"], 11))
            parts.append(svg_text(550, y, f"{score:.4g}", 11))
            y += 18
        y += 20
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def save_plots(metrics: pd.DataFrame, curves: dict, important: pd.DataFrame, target_names: list[str]) -> dict[str, Path]:
    paths = {
        "metric_comparison": REPORTS_DIR / f"{PREFIX}_metric_comparison.svg",
        "confusion_matrix": REPORTS_DIR / f"{PREFIX}_confusion_matrix.svg",
        "roc_pr_curves": REPORTS_DIR / f"{PREFIX}_roc_pr_curves.svg",
        "important_genes": REPORTS_DIR / f"{PREFIX}_important_genes.svg",
    }
    write_metric_svg(metrics, paths["metric_comparison"])
    write_confusion_svg(metrics, target_names, paths["confusion_matrix"])
    write_curve_svg(curves, paths["roc_pr_curves"])
    write_important_svg(important, paths["important_genes"])
    return paths


def markdown_table(df: pd.DataFrame) -> str:
    display_df = df.copy()
    columns = list(display_df.columns)
    lines = ["| " + " | ".join(map(str, columns)) + " |"]
    lines.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for _, row in display_df.iterrows():
        values = []
        for col in columns:
            value = row[col]
            if isinstance(value, float):
                value = f"{value:.4g}"
            values.append(str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_notebook(summary: dict, metrics: pd.DataFrame, important: pd.DataFrame, split_table: pd.DataFrame, plot_paths: dict):
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    }
    cells = []

    def md(text: str):
        cells.append(nbf.v4.new_markdown_cell(text.strip() + "\n"))

    metric_cols = [
        "model",
        "accuracy",
        "balanced_accuracy",
        "roc_auc",
        "pr_auc",
        "normal_precision",
        "normal_recall",
        "normal_f1",
        "normal_support",
        "tumor_precision",
        "tumor_recall",
        "tumor_f1",
        "tumor_support",
    ]
    metrics_display = metrics[metric_cols].copy()
    for col in metrics_display.select_dtypes(include="number").columns:
        if not col.endswith("support"):
            metrics_display[col] = metrics_display[col].round(4)
    top_genes = important.groupby("model", observed=True).head(10).copy()
    top_genes["importance_score"] = top_genes["importance_score"].round(6)

    md(
        """# TCGA Adjacent Normal Model Report / TCGA 癌旁正常样本模型报告

This report trains and compares tumor vs adjacent normal models using only TCGA COAD data from `tcga_coad` local files.

这份报告只使用 TCGA COAD 数据：Primary Tumor（原发肿瘤）和 Solid Tissue Normal（癌旁正常组织 / adjacent normal）。它不会覆盖原来的 GTEx normal report.

**Main point / 重点：** this is a stricter check than TCGA tumor + GTEx normal, because both classes come from the same TCGA COAD STAR counts source."""
    )
    md(
        f"""## Dataset / 数据集

| item | value |
| --- | --- |
| Tumor samples | {summary['tumor_samples']} |
| Adjacent normal samples | {summary['normal_samples']} |
| Protein-coding genes before filtering | {summary['shared_genes']} |
| Model genes after filtering | {summary['model_genes']} |
| Tumor source | {summary['tumor_source']} |
| Normal source | {summary['normal_source']} |

Notes:

{chr(10).join(f"- {note}" for note in summary['notes'])}"""
    )
    md("## Train/Test Split / 训练测试划分\n\n" + markdown_table(split_table))
    md(
        """## Model Comparison / 模型对比

`balanced_accuracy` is important because the normal class is small. `normal_recall` tells us how many real adjacent normal samples were correctly found.

`balanced_accuracy`（平衡准确率）很重要，因为 normal 类别很小。`normal_recall` 表示真正的癌旁正常样本里，有多少被模型找出来。

"""
        + markdown_table(metrics_display)
    )
    md(f"## Metric Plot / 指标图\n\n![Metric comparison]({plot_paths['metric_comparison'].name})")
    md(f"## Confusion Matrices / 混淆矩阵\n\n![Confusion matrix]({plot_paths['confusion_matrix'].name})")
    md(f"## ROC And PR Curves / ROC 与 PR 曲线\n\n![ROC and PR curves]({plot_paths['roc_pr_curves'].name})")
    md(
        """## Important Genes / 重要基因

These genes are predictive features, not proven causal cancer genes. Use them as candidates for literature review.

这些基因只是模型用来预测的特征，不等于已经证明它们导致癌症。

"""
        + markdown_table(top_genes[["model", "rank", "gene_symbol", "importance_score", "direction"]])
    )
    md(f"![Important genes]({plot_paths['important_genes'].name})")
    md(
        """## Interpretation / 结果解释

This TCGA-only adjacent-normal report is more meaningful than mixing TCGA tumor with GTEx normal, because both labels come from the same TCGA COAD STAR counts data source. However, the normal group is still small, so the test set contains only a few adjacent normal samples. One normal-sample mistake can change the score a lot.

这份 TCGA-only 癌旁正常报告比 TCGA tumor + GTEx normal 更有解释价值，因为 tumor 和 normal 来自同一个 TCGA COAD STAR counts 数据源。但 normal 只有 41 个，所以测试集里的 normal 很少；一个 normal 样本预测错了，分数就会变化很大。

Recommended reading: compare this report with the GTEx report. If GTEx is perfect but TCGA-only is lower, that supports the idea that the GTEx result was partly inflated by source/cohort effects."""
    )
    nb.cells = cells
    nbf.write(nb, REPORTS_DIR / f"{PREFIX}_model_report.ipynb")


def sync_outputs(paths: list[Path]) -> None:
    JUPYTER_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    JUPYTER_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if path.exists():
            target_dir = JUPYTER_MODELS_DIR if path.suffix == ".pkl" else JUPYTER_REPORTS_DIR
            target = target_dir / path.name
            target.write_bytes(path.read_bytes())


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    metadata = load_metadata()
    features, labels = build_feature_matrix(metadata)
    model_features, y, encoder, train_idx, test_idx = prepare_model_inputs(features, labels)

    trained = []
    for name, pipeline in model_definitions().items():
        pipeline.fit(model_features.iloc[train_idx], y[train_idx])
        model_path = MODELS_DIR / f"{PREFIX}_{name}.pkl"
        model_path.write_bytes(
            pickle.dumps(
                {
                "model_name": name,
                "pipeline": pipeline,
                "features": list(model_features.columns),
                "random_state": RANDOM_STATE,
                "data_source": "TCGA COAD Primary Tumor vs Solid Tissue Normal",
                }
            )
        )
        trained.append(ModelResult(name=name, pipeline=pipeline, path=model_path))

    metrics, curves = evaluate_models(trained, model_features, y, encoder, test_idx)
    important = extract_important_genes(trained, list(model_features.columns))
    target_names = list(encoder.classes_)
    plot_paths = save_plots(metrics, curves, important, target_names)

    split_table = (
        pd.concat([labels.iloc[train_idx].assign(split="train"), labels.iloc[test_idx].assign(split="test")])
        .groupby(["split", "label"])
        .size()
        .rename("samples")
        .reset_index()
    )
    summary = {
        "tumor_samples": int((labels["label"] == "tumor").sum()),
        "normal_samples": int((labels["label"] == "normal").sum()),
        "shared_genes": int(features.shape[1]),
        "model_genes": int(model_features.shape[1]),
        "tumor_source": "local GDC TCGA-COAD STAR counts Primary Tumor tpm_unstranded",
        "normal_source": "local GDC TCGA-COAD STAR counts Solid Tissue Normal tpm_unstranded",
        "notes": [
            "This report uses only TCGA COAD local STAR counts files.",
            "The adjacent normal class has only 41 samples.",
            "The train/test split is stratified by label and grouped by case_submitter_id.",
            "Use balanced_accuracy, normal_recall, and confusion matrices instead of accuracy alone.",
        ],
    }

    metrics_path = REPORTS_DIR / f"{PREFIX}_metrics_summary.csv"
    important_path = REPORTS_DIR / f"{PREFIX}_important_genes.csv"
    split_path = REPORTS_DIR / f"{PREFIX}_train_test_split.csv"
    summary_path = REPORTS_DIR / f"{PREFIX}_summary.json"
    metrics.to_csv(metrics_path, index=False)
    important.to_csv(important_path, index=False)
    split_table.to_csv(split_path, index=False)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    build_notebook(summary, metrics, important, split_table, plot_paths)

    outputs = [
        metrics_path,
        important_path,
        split_path,
        summary_path,
        REPORTS_DIR / f"{PREFIX}_model_report.ipynb",
        *plot_paths.values(),
        *[result.path for result in trained],
    ]
    sync_outputs(outputs)
    print(metrics.to_string(index=False))
    print(f"Report: {REPORTS_DIR / f'{PREFIX}_model_report.ipynb'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

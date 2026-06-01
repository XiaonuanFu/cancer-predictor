from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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

from . import config


def model_scores(pipeline, X):
    if hasattr(pipeline, "predict_proba"):
        return pipeline.predict_proba(X)[:, 1]
    if hasattr(pipeline, "decision_function"):
        return pipeline.decision_function(X)
    return pipeline.predict(X)


def evaluate_models(trained_models, features, y, encoder, test_idx) -> pd.DataFrame:
    config.ensure_dirs()
    X_test = features.iloc[test_idx]
    y_test = y[test_idx]
    target_names = list(encoder.classes_)
    tumor_index = target_names.index(config.POSITIVE_LABEL)
    records = []
    curves = {}

    for trained in trained_models:
        y_pred = trained.pipeline.predict(X_test)
        scores = model_scores(trained.pipeline, X_test)
        y_binary = (y_test == tumor_index).astype(int)

        precision, recall, f1_by_class, support = precision_recall_fscore_support(
            y_test,
            y_pred,
            labels=list(range(len(target_names))),
            zero_division=0,
        )
        cm = confusion_matrix(y_test, y_pred, labels=list(range(len(target_names))))

        record = {
            "model": trained.name,
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
        curves[trained.name] = {
            "fpr": fpr,
            "tpr": tpr,
            "precision": pr_precision,
            "recall": pr_recall,
            "cm": cm,
        }

    metrics = pd.DataFrame(records)
    metrics.to_csv(config.METRICS_FILE, index=False)
    plot_curves(curves)
    plot_confusion_matrix(curves, target_names)
    return metrics


def plot_curves(curves: dict) -> None:
    plt.figure(figsize=(7, 5))
    for name, curve in curves.items():
        plt.plot(curve["fpr"], curve["tpr"], label=name)
    plt.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig(config.ROC_CURVE_FILE, dpi=160)
    plt.close()

    plt.figure(figsize=(7, 5))
    for name, curve in curves.items():
        plt.plot(curve["recall"], curve["precision"], label=name)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig(config.PR_CURVE_FILE, dpi=160)
    plt.close()


def plot_confusion_matrix(curves: dict, target_names: list[str]) -> None:
    n = len(curves)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4))
    if n == 1:
        axes = [axes]
    for ax, (name, curve) in zip(axes, curves.items()):
        cm = curve["cm"]
        im = ax.imshow(cm, cmap="Blues")
        ax.set_title(name)
        ax.set_xticks(np.arange(len(target_names)), target_names, rotation=30)
        ax.set_yticks(np.arange(len(target_names)), target_names)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="black")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(config.CONFUSION_MATRIX_FILE, dpi=160)
    plt.close(fig)


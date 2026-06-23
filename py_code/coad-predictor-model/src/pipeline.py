from __future__ import annotations

import argparse

import pandas as pd

from . import config
from .data import build_prepared_data, load_prepared_features
from .evaluate import evaluate_models
from .interpret import extract_important_genes, write_model_report
from .preprocessing import prepare_model_inputs
from .train import train_models


def prepare() -> None:
    prepared = build_prepared_data()
    print(
        "Prepared data:",
        f"samples={prepared.features.shape[0]}",
        f"genes={prepared.features.shape[1]}",
        f"tumor={prepared.summary['tumor_samples']}",
        f"normal={prepared.summary['normal_samples']}",
    )


def train_and_report() -> None:
    config.ensure_dirs()
    features, labels = load_prepared_features()
    model_features, y, encoder, train_idx, test_idx = prepare_model_inputs(features, labels)
    model_features.to_parquet(config.FEATURES_FILE)
    config.SELECTED_GENES_FILE.write_text("\n".join(model_features.columns) + "\n", encoding="utf-8")
    trained = train_models(model_features, y, train_idx)
    metrics = evaluate_models(trained, model_features, y, encoder, test_idx)
    important = extract_important_genes(trained, list(model_features.columns))
    write_model_report(metrics, important)
    print("Trained models:", ", ".join(t.name for t in trained))
    print(f"Metrics written to {config.METRICS_FILE}")
    print(f"Report written to {config.MODEL_REPORT_FILE}")


def all_steps() -> None:
    prepare()
    train_and_report()


def main() -> int:
    parser = argparse.ArgumentParser(description="COAD tumor/normal model pipeline")
    parser.add_argument("step", choices=["prepare", "train", "report", "all"], help="Pipeline step to run")
    args = parser.parse_args()

    if args.step == "prepare":
        prepare()
    elif args.step in {"train", "report"}:
        train_and_report()
    elif args.step == "all":
        all_steps()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


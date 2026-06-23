from __future__ import annotations

from dataclasses import dataclass

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

from . import config


@dataclass(frozen=True)
class TrainedModel:
    name: str
    pipeline: Pipeline
    path: object


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
                        random_state=config.RANDOM_STATE,
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
                        random_state=config.RANDOM_STATE,
                        n_jobs=-1,
                    ),
                )
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
                        random_state=config.RANDOM_STATE,
                        max_iter=10000,
                        dual=True,
                    ),
                ),
            ]
        ),
    }


def train_models(features: pd.DataFrame, y, train_idx) -> list[TrainedModel]:
    config.ensure_dirs()
    trained = []
    X_train = features.iloc[train_idx]
    y_train = y[train_idx]
    for name, pipeline in model_definitions().items():
        pipeline.fit(X_train, y_train)
        path = config.MODELS_DIR / f"{name}.joblib"
        joblib.dump(
            {
                "model_name": name,
                "pipeline": pipeline,
                "features": list(features.columns),
                "random_state": config.RANDOM_STATE,
            },
            path,
        )
        trained.append(TrainedModel(name=name, pipeline=pipeline, path=path))
    return trained

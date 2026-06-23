from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold
from sklearn.preprocessing import LabelEncoder

from . import config


def log2_transform(features: pd.DataFrame) -> pd.DataFrame:
    clipped = features.clip(lower=0)
    return np.log2(clipped + 1.0)


def remove_low_variance(features: pd.DataFrame, threshold: float = 1e-8) -> pd.DataFrame:
    variances = features.var(axis=0, skipna=True)
    keep = variances[variances > threshold].index
    return features.loc[:, keep]


def encode_labels(labels: pd.Series) -> tuple[np.ndarray, LabelEncoder]:
    encoder = LabelEncoder()
    y = encoder.fit_transform(labels)
    return y, encoder


def make_train_test_split(labels: pd.DataFrame):
    y, encoder = encode_labels(labels["label"])
    groups = labels["case_submitter_id"].fillna(labels["sample_id"]).astype(str).to_numpy()
    idx = np.arange(len(labels))

    try:
        splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=config.RANDOM_STATE)
        train_idx, test_idx = next(splitter.split(idx, y, groups))
    except Exception:
        splitter = GroupShuffleSplit(
            n_splits=1,
            test_size=config.TEST_SIZE,
            random_state=config.RANDOM_STATE,
        )
        train_idx, test_idx = next(splitter.split(idx, y, groups))

    labels.iloc[train_idx].to_csv(config.TRAIN_SAMPLES_FILE, index=False)
    labels.iloc[test_idx].to_csv(config.TEST_SAMPLES_FILE, index=False)
    return train_idx, test_idx, y, encoder


def prepare_model_inputs(features: pd.DataFrame, labels: pd.DataFrame):
    transformed = log2_transform(features)
    transformed = remove_low_variance(transformed)
    train_idx, test_idx, y, encoder = make_train_test_split(labels)
    return transformed, y, encoder, train_idx, test_idx


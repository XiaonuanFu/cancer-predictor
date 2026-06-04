from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


RANDOM_STATE = 42
TARGET_COLUMN = "exam_score"
ID_COLUMNS = ["student_id"]
DATA_FILE = "student_habits_performance.csv"


def resolve_data_path() -> Path:
    workspace_root = Path(__file__).resolve().parents[2]
    candidates = [
        workspace_root / "data" / "ml_data" / DATA_FILE,
        Path("/workspace/data/ml_data") / DATA_FILE,
        Path.cwd() / "data" / "ml_data" / DATA_FILE,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    paths = "\n".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Could not find {DATA_FILE}. Checked:\n{paths}")


def build_pipeline(numeric_features: list[str], categorical_features: list[str]) -> Pipeline:
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_transformer, numeric_features),
            ("categorical", categorical_transformer, categorical_features),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=300,
                    max_depth=12,
                    min_samples_leaf=3,
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def feature_names(model: Pipeline) -> list[str]:
    return model.named_steps["preprocess"].get_feature_names_out().tolist()


def main() -> None:
    data_path = resolve_data_path()
    df = pd.read_csv(data_path)

    feature_df = df.drop(columns=[TARGET_COLUMN, *ID_COLUMNS], errors="ignore")
    target = df[TARGET_COLUMN]

    numeric_features = feature_df.select_dtypes(include=["number"]).columns.tolist()
    categorical_features = feature_df.select_dtypes(exclude=["number"]).columns.tolist()

    x_train, x_test, y_train, y_test = train_test_split(
        feature_df,
        target,
        test_size=0.2,
        random_state=RANDOM_STATE,
    )

    model = build_pipeline(numeric_features, categorical_features)
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)

    importances = model.named_steps["model"].feature_importances_
    top_features = (
        pd.DataFrame({"feature": feature_names(model), "importance": importances})
        .sort_values("importance", ascending=False)
        .head(10)
    )

    print("Student exam score prediction - Random Forest Regressor")
    print(f"Data file: {data_path}")
    print(f"Rows: {len(df)}")
    print(f"Features: {feature_df.shape[1]} ({len(numeric_features)} numeric, {len(categorical_features)} categorical)")
    print(f"Target: {TARGET_COLUMN}")
    print("\nTest metrics")
    print(f"MAE:  {mae:.3f}")
    print(f"RMSE: {rmse:.3f}")
    print(f"R2:   {r2:.3f}")
    print("\nTop random forest feature importances")
    print(top_features.to_string(index=False))


if __name__ == "__main__":
    main()

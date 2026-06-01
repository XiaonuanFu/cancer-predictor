from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"

DB_HOST = "bio-postgres"
DB_PORT = 5432
DB_NAME = "bio"
DB_USER = "bio"
DB_PASSWORD = "bioanalysis"

RANDOM_STATE = 42
TEST_SIZE = 0.2
POSITIVE_LABEL = "tumor"

FEATURES_FILE = DATA_DIR / "coad_tumor_normal_features.parquet"
RAW_FEATURES_FILE = DATA_DIR / "coad_tumor_normal_raw_expression.parquet"
LABELS_FILE = DATA_DIR / "coad_tumor_normal_labels.csv"
SELECTED_GENES_FILE = DATA_DIR / "coad_selected_genes.txt"
TRAIN_SAMPLES_FILE = DATA_DIR / "train_samples.csv"
TEST_SAMPLES_FILE = DATA_DIR / "test_samples.csv"
DATA_SUMMARY_FILE = DATA_DIR / "data_summary.json"

METRICS_FILE = REPORTS_DIR / "metrics_summary.csv"
IMPORTANT_GENES_FILE = REPORTS_DIR / "important_genes.csv"
MODEL_REPORT_FILE = REPORTS_DIR / "model_report.md"
CONFUSION_MATRIX_FILE = REPORTS_DIR / "confusion_matrix.png"
ROC_CURVE_FILE = REPORTS_DIR / "roc_curve.png"
PR_CURVE_FILE = REPORTS_DIR / "pr_curve.png"


def ensure_dirs() -> None:
    for path in (DATA_DIR, MODELS_DIR, REPORTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def db_url() -> str:
    return f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

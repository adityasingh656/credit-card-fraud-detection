"""
Batch Fraud Prediction CLI Tool.
Evaluates CSV files of credit card transactions using the trained Isolation Forest model.
Supports local SQLite logging, optional MySQL persistence, and CSV export.
"""

import argparse
import json
import os
import sys
from pathlib import Path
import joblib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Paths
MODEL_PATH = PROJECT_ROOT / "models" / "final_isolation_forest.pkl"
SCALER_PATH = PROJECT_ROOT / "models" / "final_scaler.pkl"
THRESHOLD_PATH = PROJECT_ROOT / "models" / "fraud_threshold.pkl"
SQLITE_PATH = PROJECT_ROOT / "backend" / "fraud_records.db"

# Features
FEATURES = [
    "Time",
    "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10",
    "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19",
    "V20", "V21", "V22", "V23", "V24", "V25", "V26", "V27", "V28",
    "Amount"
]


def load_model_artifacts():
    """Loads Isolation Forest model, Scaler, and optimal Threshold."""
    if not (MODEL_PATH.exists() and SCALER_PATH.exists() and THRESHOLD_PATH.exists()):
        raise FileNotFoundError(
            f"Missing required model artifacts in {PROJECT_ROOT / 'models'}. Please ensure models are present."
        )

    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    threshold = float(joblib.load(THRESHOLD_PATH))
    return model, scaler, threshold


def predict_transactions(data: pd.DataFrame, model, scaler, threshold: float) -> pd.DataFrame:
    """Calculates anomaly score and assigns fraud classifications."""
    missing = [f for f in FEATURES if f not in data.columns]
    if missing:
        raise ValueError(f"Input CSV is missing required features: {missing}")

    X = data[FEATURES].copy()
    X["Amount"] = scaler.transform(X[["Amount"]])

    decision_scores = model.decision_function(X)
    anomaly_scores = -decision_scores

    predictions = (anomaly_scores >= threshold).astype(int)

    result = data.copy()
    result["anomaly_score"] = anomaly_scores
    result["predicted_fraud"] = predictions
    result["prediction"] = result["predicted_fraud"].map({0: "LEGITIMATE", 1: "FRAUD"})
    result["threshold"] = threshold

    return result


def save_to_sqlite(result: pd.DataFrame):
    """Saves predictions to local SQLite database."""
    import sqlite3

    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            time_val REAL,
            amount REAL,
            anomaly_score REAL,
            threshold REAL,
            predicted_fraud INTEGER,
            prediction TEXT,
            risk_level TEXT,
            risk_percentage REAL,
            source TEXT,
            top_features TEXT
        )
    """)

    rows = []
    for _, row in result.iterrows():
        is_fraud = int(row["predicted_fraud"])
        risk_level = "CRITICAL" if is_fraud else "LOW"
        risk_pct = 85.0 if is_fraud else 15.0

        rows.append((
            float(row["Time"]),
            float(row["Amount"]),
            float(row["anomaly_score"]),
            float(row["threshold"]),
            is_fraud,
            str(row["prediction"]),
            risk_level,
            risk_pct,
            "cli_tool",
            json.dumps([])
        ))

    cursor.executemany("""
        INSERT INTO transactions (
            time_val, amount, anomaly_score, threshold,
            predicted_fraud, prediction, risk_level, risk_percentage,
            source, top_features
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()
    print(f"✓ Saved {len(rows)} predictions to SQLite ({SQLITE_PATH.name}).")


def save_to_mysql(result: pd.DataFrame, host="127.0.0.1", port=3306, user="root", password=None, database="credit_card_fraud"):
    """Optional MySQL sync with graceful connection fallback."""
    try:
        import mysql.connector
        pwd = password or os.getenv("MYSQL_PASSWORD") or "Fraud@2026"
        p = int(os.getenv("MYSQL_PORT", port))

        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", host),
            port=p,
            user=os.getenv("MYSQL_USER", user),
            password=pwd,
            database=os.getenv("MYSQL_DATABASE", database),
            connect_timeout=3
        )
        cursor = conn.cursor()

        columns = [
            "Time", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10",
            "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19", "V20",
            "V21", "V22", "V23", "V24", "V25", "V26", "V27", "V28", "Amount",
            "actual_class", "anomaly_score", "predicted_fraud"
        ]
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO transactions ({', '.join(columns)}) VALUES ({placeholders})"

        for _, row in result.iterrows():
            vals = tuple(row[c] for c in columns[:-3]) + (
                None,
                float(row["anomaly_score"]),
                int(row["predicted_fraud"])
            )
            cursor.execute(query, vals)

        conn.commit()
        conn.close()
        print(f"✓ Saved {len(result)} predictions to MySQL ({database}).")
    except Exception as e:
        print(f"ℹ MySQL sync skipped ({e}). Result preserved in SQLite and CSV.")


def main():
    parser = argparse.ArgumentParser(
        description="AEGIS AI - Credit Card Fraud Prediction CLI"
    )
    parser.add_argument("csv_path", help="Path to transaction CSV file to evaluate")
    parser.add_argument("--export", help="Custom destination for output CSV", default=None)
    parser.add_argument("--db", choices=["sqlite", "mysql", "both", "none"], default="sqlite", help="Database persistence target")

    args = parser.parse_args()
    csv_file = Path(args.csv_path)

    if not csv_file.exists():
        print(f"Error: Input file '{csv_file}' not found.")
        sys.exit(1)

    print("=" * 65)
    print("      AEGIS // CREDIT CARD FRAUD DETECTION CLI ENGINE")
    print("=" * 65)

    model, scaler, threshold = load_model_artifacts()
    print(f"Model: Isolation Forest | Fraud Decision Threshold: {threshold:.6f}")

    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} transactions from '{csv_file.name}'.")

    result = predict_transactions(df, model, scaler, threshold)

    frauds = result[result["predicted_fraud"] == 1]
    cleans = result[result["predicted_fraud"] == 0]

    print("\nBatch Evaluation Summary:")
    print("-" * 65)
    print(f"Total Transactions : {len(result)}")
    print(f"🚨 FRAUD DETECTED   : {len(frauds)} ({(len(frauds) / len(result) * 100):.1f}%)")
    print(f"🛡️  LEGITIMATE       : {len(cleans)} ({(len(cleans) / len(result) * 100):.1f}%)")
    print(f"Total Value at Risk: ${frauds['Amount'].sum():,.2f}")

    # Output CSV
    out_path = Path(args.export) if args.export else csv_file.parent / f"{csv_file.stem}_predictions.csv"
    result.to_csv(out_path, index=False)
    print(f"\n✓ Output CSV saved to: {out_path}")

    # Database logging
    if args.db in ["sqlite", "both"]:
        save_to_sqlite(result)
    if args.db in ["mysql", "both"]:
        save_to_mysql(result)

    print("\nEvaluation completed successfully.")


if __name__ == "__main__":
    main()

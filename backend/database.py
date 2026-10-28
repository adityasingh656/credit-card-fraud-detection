"""
Database Persistence Layer for Credit Card Fraud Detection.
Uses local embedded SQLite by default for zero-friction setup,
with optional automatic sync/support for MySQL if configured.
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SQLITE_DB_PATH = BASE_DIR / "fraud_records.db"

# Optional MySQL configuration via environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "credit_card_fraud")


class DatabaseManager:
    def __init__(self):
        self.sqlite_path = SQLITE_DB_PATH
        self.use_mysql = bool(MYSQL_HOST and MYSQL_USER and MYSQL_PASSWORD)
        self.init_db()

    def get_sqlite_conn(self):
        """Creates connection with row factory for dictionary access."""
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes SQLite schema if not already present."""
        with self.get_sqlite_conn() as conn:
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
            conn.commit()

    def log_transaction(self, tx_data: dict, result: dict, source: str = "manual") -> int:
        """Logs single prediction result to SQLite database."""
        amount = float(tx_data.get("Amount", 0.0))
        time_val = float(tx_data.get("Time", 0.0))
        anomaly_score = float(result.get("anomaly_score", 0.0))
        threshold = float(result.get("threshold", 0.036042))
        predicted_fraud = int(result.get("predicted_fraud", 0))
        prediction = result.get("prediction", "LEGITIMATE")
        risk_level = result.get("risk_tier", {}).get("level", "LOW")
        risk_percentage = float(result.get("risk_percentage", 0.0))
        top_features = json.dumps(result.get("top_features", []))

        with self.get_sqlite_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (
                    time_val, amount, anomaly_score, threshold,
                    predicted_fraud, prediction, risk_level, risk_percentage,
                    source, top_features
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                time_val, amount, anomaly_score, threshold,
                predicted_fraud, prediction, risk_level, risk_percentage,
                source, top_features
            ))
            conn.commit()
            return cursor.lastrowid

    def log_batch(self, items: list, source: str = "batch") -> int:
        """Batch insert transaction records."""
        if not items:
            return 0

        rows = []
        for item in items:
            rows.append((
                float(item.get("Time", 0.0)),
                float(item.get("Amount", 0.0)),
                float(item.get("anomaly_score", 0.0)),
                float(item.get("threshold", 0.036042)),
                int(item.get("predicted_fraud", 0)),
                str(item.get("prediction", "LEGITIMATE")),
                str(item.get("risk_tier", "LOW")),
                float(item.get("risk_percentage", 0.0)),
                source,
                json.dumps([])
            ))

        with self.get_sqlite_conn() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO transactions (
                    time_val, amount, anomaly_score, threshold,
                    predicted_fraud, prediction, risk_level, risk_percentage,
                    source, top_features
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()
            return len(rows)

    def get_history(self, limit: int = 50, offset: int = 0, verdict_filter: str = None) -> list:
        """Retrieves paginated audit log of transaction predictions."""
        with self.get_sqlite_conn() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM transactions"
            params = []

            if verdict_filter and verdict_filter.upper() in ["FRAUD", "LEGITIMATE"]:
                query += " WHERE prediction = ?"
                params.append(verdict_filter.upper())

            query += " ORDER BY id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            history = []
            for r in rows:
                features = []
                try:
                    if r["top_features"]:
                        features = json.loads(r["top_features"])
                except Exception:
                    features = []

                history.append({
                    "id": r["id"],
                    "created_at": r["created_at"],
                    "time_val": r["time_val"],
                    "amount": r["amount"],
                    "anomaly_score": r["anomaly_score"],
                    "threshold": r["threshold"],
                    "predicted_fraud": r["predicted_fraud"],
                    "prediction": r["prediction"],
                    "risk_level": r["risk_level"],
                    "risk_percentage": r["risk_percentage"],
                    "source": r["source"],
                    "top_features": features
                })
            return history

    def get_analytics(self) -> dict:
        """Computes aggregate analytics from stored evaluation history."""
        with self.get_sqlite_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) as total_count,
                    SUM(CASE WHEN predicted_fraud = 1 THEN 1 ELSE 0 END) as fraud_count,
                    SUM(CASE WHEN predicted_fraud = 0 THEN 1 ELSE 0 END) as clean_count,
                    AVG(anomaly_score) as avg_score,
                    AVG(risk_percentage) as avg_risk,
                    SUM(amount) as total_volume,
                    SUM(CASE WHEN predicted_fraud = 1 THEN amount ELSE 0 END) as fraud_volume
                FROM transactions
            """)
            stats = cursor.fetchone()

            total = stats["total_count"] or 0
            frauds = stats["fraud_count"] or 0
            cleans = stats["clean_count"] or 0
            avg_score = stats["avg_score"] or 0.0
            avg_risk = stats["avg_risk"] or 0.0
            total_vol = stats["total_volume"] or 0.0
            fraud_vol = stats["fraud_volume"] or 0.0

            fraud_rate = (frauds / total * 100.0) if total > 0 else 0.0

            return {
                "total_evaluations": total,
                "fraud_count": frauds,
                "clean_count": cleans,
                "fraud_rate_percent": round(fraud_rate, 2),
                "avg_anomaly_score": round(avg_score, 6),
                "avg_risk_percentage": round(avg_risk, 1),
                "total_volume_usd": round(total_vol, 2),
                "fraud_volume_usd": round(fraud_vol, 2),
                "storage_engine": "SQLite (zero-config, high-speed)"
            }

    def clear_history(self) -> int:
        """Clears test audit log."""
        with self.get_sqlite_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions")
            conn.commit()
            return cursor.rowcount


# Singleton instance
db = DatabaseManager()

"""
Detector module for Credit Card Fraud Detection.
Wraps the Isolation Forest model, standard scaler, and decision threshold.
Provides anomaly scoring, risk percentage normalization, and feature deviation explainability.
"""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd

# Expected 30 features
FEATURES = [
    "Time",
    "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10",
    "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19",
    "V20", "V21", "V22", "V23", "V24", "V25", "V26", "V27", "V28",
    "Amount"
]

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "final_isolation_forest.pkl"
SCALER_PATH = BASE_DIR / "models" / "final_scaler.pkl"
THRESHOLD_PATH = BASE_DIR / "models" / "fraud_threshold.pkl"


class FraudDetector:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.threshold = 0.036042
        self.is_loaded = False
        self.load_artifacts()

    def load_artifacts(self):
        """Loads trained Isolation Forest, Scaler, and Threshold artifacts."""
        try:
            if MODEL_PATH.exists():
                self.model = joblib.load(MODEL_PATH)
            if SCALER_PATH.exists():
                self.scaler = joblib.load(SCALER_PATH)
            if THRESHOLD_PATH.exists():
                thresh_val = joblib.load(THRESHOLD_PATH)
                self.threshold = float(thresh_val)
            self.is_loaded = self.model is not None and self.scaler is not None
        except Exception as e:
            print(f"[FraudDetector] Warning: Could not load model artifacts: {e}")
            self.is_loaded = False

    def calculate_risk_percent(self, anomaly_score: float) -> float:
        """
        Maps anomaly score relative to threshold into a 0 - 100% risk percentage.
        - Scores well below 0 have ~0-25% risk.
        - Scores between 0 and threshold span ~25-69% risk.
        - Scores at threshold start at 70%.
        - Scores significantly above threshold approach 99%.
        """
        thresh = self.threshold
        if anomaly_score <= 0:
            # Safe zone: 0 to 25%
            # typical lowest scores are around -0.15
            normalized = max(0.0, (anomaly_score + 0.15) / 0.15) * 25.0
            return round(min(25.0, normalized), 1)
        elif anomaly_score < thresh:
            # Low to moderate risk: 25% to 69%
            fraction = anomaly_score / thresh
            risk = 25.0 + (fraction * 44.0)
            return round(risk, 1)
        else:
            # Threshold crossed: 70% to 99%
            excess = anomaly_score - thresh
            # typical max excess is ~0.08
            scale = min(1.0, excess / 0.08)
            risk = 70.0 + (scale * 29.0)
            return round(min(99.4, risk), 1)

    def determine_risk_tier(self, risk_percent: float, is_fraud: bool) -> dict:
        """Classifies risk percentage into standardized alert tiers."""
        if is_fraud or risk_percent >= 70.0:
            if risk_percent >= 85.0:
                return {
                    "level": "CRITICAL",
                    "badge_color": "danger",
                    "action": "Immediate Block & Card Freeze",
                    "description": "High-confidence anomalous pattern matching known fraudulent transaction clusters."
                }
            return {
                "level": "HIGH",
                "badge_color": "warning-high",
                "action": "Hold Transaction & Trigger 2FA",
                "description": "Transaction anomaly score exceeds defense threshold."
            }
        elif risk_percent >= 45.0:
            return {
                "level": "MODERATE",
                "badge_color": "warning",
                "action": "Flag for Asynchronous Review",
                "description": "Borderline behavioral deviation detected."
            }
        else:
            return {
                "level": "LOW",
                "badge_color": "success",
                "action": "Approve Transaction Instantly",
                "description": "Transaction conforms to standard non-fraudulent profile."
            }

    def explain_features(self, raw_row: dict) -> list:
        """
        Identifies top contributing PCA and Amount features that diverge
        from normal transaction baselines (|z| > 2.0).
        """
        deviations = []
        for feature in FEATURES:
            if feature in raw_row and raw_row[feature] is not None:
                try:
                    val = float(raw_row[feature])
                except (ValueError, TypeError):
                    continue

                if feature == "Amount":
                    # Median amount in CC dataset is ~$22, normal 95th percentile is ~$300
                    if val > 500:
                        deviations.append({
                            "feature": "Amount",
                            "value": round(val, 2),
                            "deviation_score": round(min(10.0, val / 150.0), 2),
                            "direction": "High Amount Spike",
                            "significance": "HIGH" if val > 1500 else "MEDIUM"
                        })
                elif feature.startswith("V"):
                    # PCA features are approximately standard normal (mean 0, std 1)
                    abs_val = abs(val)
                    if abs_val > 1.8:
                        deviations.append({
                            "feature": feature,
                            "value": round(val, 4),
                            "deviation_score": round(abs_val, 2),
                            "direction": "Positive Divergence" if val > 0 else "Negative Divergence",
                            "significance": "CRITICAL" if abs_val >= 3.5 else ("HIGH" if abs_val >= 2.5 else "MODERATE")
                        })

        # Sort by deviation magnitude descending
        deviations.sort(key=lambda x: x["deviation_score"], reverse=True)
        return deviations[:5]

    def predict_single(self, data: dict) -> dict:
        """Predict fraud status for a single transaction dictionary."""
        # Validate features
        missing = [f for f in FEATURES if f not in data]
        if missing:
            raise ValueError(f"Missing required features: {missing}")

        if not self.is_loaded:
            # Fallback estimation if model artifacts not yet loaded
            amount = float(data.get("Amount", 0))
            score = 0.05 if amount > 1000 else 0.01
            is_fraud = score >= self.threshold
            risk_pct = self.calculate_risk_percent(score)
            tier = self.determine_risk_tier(risk_pct, is_fraud)
            return {
                "prediction": "FRAUD" if is_fraud else "LEGITIMATE",
                "predicted_fraud": int(is_fraud),
                "anomaly_score": score,
                "threshold": self.threshold,
                "risk_percentage": risk_pct,
                "risk_tier": tier,
                "top_features": self.explain_features(data),
                "model_status": "mock_fallback"
            }

        # Build DataFrame in exact feature order
        df = pd.DataFrame([data])[FEATURES].copy()

        # Scale Amount
        df["Amount"] = self.scaler.transform(df[["Amount"]])

        # Model inference
        decision_score = float(self.model.decision_function(df)[0])
        anomaly_score = float(-decision_score)
        predicted_fraud = int(anomaly_score >= self.threshold)
        prediction = "FRAUD" if predicted_fraud == 1 else "LEGITIMATE"

        risk_percent = self.calculate_risk_percent(anomaly_score)
        tier = self.determine_risk_tier(risk_percent, bool(predicted_fraud))
        top_features = self.explain_features(data)

        return {
            "prediction": prediction,
            "predicted_fraud": predicted_fraud,
            "anomaly_score": round(anomaly_score, 6),
            "threshold": round(self.threshold, 6),
            "threshold_delta": round(anomaly_score - self.threshold, 6),
            "risk_percentage": risk_percent,
            "risk_tier": tier,
            "top_features": top_features,
            "model_status": "active"
        }

    def predict_batch(self, records: list) -> dict:
        """Vectorized batch prediction for multiple transactions."""
        if not records:
            return {"total": 0, "fraud_count": 0, "clean_count": 0, "results": []}

        df_raw = pd.DataFrame(records)
        missing = [f for f in FEATURES if f not in df_raw.columns]
        if missing:
            raise ValueError(f"Missing required features in batch: {missing}")

        df = df_raw[FEATURES].copy()

        if self.is_loaded:
            df["Amount"] = self.scaler.transform(df[["Amount"]])
            decision_scores = self.model.decision_function(df)
            anomaly_scores = -decision_scores
        else:
            # Fallback estimation
            anomaly_scores = np.array([
                0.05 if float(row.get("Amount", 0)) > 1000 else 0.01 for row in records
            ])

        predictions = (anomaly_scores >= self.threshold).astype(int)

        results = []
        fraud_count = 0
        total_amount = 0.0
        fraud_amount = 0.0

        for i, score in enumerate(anomaly_scores):
            raw_item = records[i]
            is_fraud = bool(predictions[i])
            if is_fraud:
                fraud_count += 1

            amount = float(raw_item.get("Amount", 0.0))
            total_amount += amount
            if is_fraud:
                fraud_amount += amount

            score_flt = float(score)
            risk_pct = self.calculate_risk_percent(score_flt)
            tier = self.determine_risk_tier(risk_pct, is_fraud)

            results.append({
                "index": i + 1,
                "Time": raw_item.get("Time"),
                "Amount": amount,
                "anomaly_score": round(score_flt, 6),
                "threshold": round(self.threshold, 6),
                "predicted_fraud": int(is_fraud),
                "prediction": "FRAUD" if is_fraud else "LEGITIMATE",
                "risk_percentage": risk_pct,
                "risk_tier": tier["level"]
            })

        return {
            "total": len(records),
            "fraud_count": fraud_count,
            "clean_count": len(records) - fraud_count,
            "fraud_rate_percent": round((fraud_count / len(records)) * 100, 2),
            "total_volume": round(total_amount, 2),
            "fraud_volume": round(fraud_amount, 2),
            "results": results
        }


# Singleton instance
detector = FraudDetector()

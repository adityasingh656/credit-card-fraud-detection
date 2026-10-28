"""
Credit Card Fraud Detection Backend API
Enterprise Flask Server with Isolation Forest ML Engine, SQLite/MySQL Persistence,
Batch Processing, Explanations, Presets, and RESTful Analytics Endpoints.
"""

from datetime import datetime
import io
import time
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, send_file
import pandas as pd

from detector import detector, FEATURES
from database import db
from presets import SAMPLE_PRESETS

# Root directory
BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    static_folder="../frontend",
    static_url_path=""
)

# Start time for uptime reporting
START_TIME = time.time()


# -------------------------------------------------------------
# CORS & Request Headers Middleware
# -------------------------------------------------------------
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


# -------------------------------------------------------------
# Frontend Static Routes
# -------------------------------------------------------------
@app.route("/")
def index():
    """Serves the main cyber-fintech dashboard."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_proxy(path):
    """Serves styles, scripts, and static assets."""
    return send_from_directory(app.static_folder, path)


# -------------------------------------------------------------
# System Status & Health Check
# -------------------------------------------------------------
@app.route("/api/status", methods=["GET"])
def get_status():
    """Returns system health, ML model metadata, and operational stats."""
    uptime_seconds = int(time.time() - START_TIME)
    analytics = db.get_analytics()

    return jsonify({
        "status": "healthy",
        "system": "AEGIS RiskOps Fraud Detection Platform",
        "version": "2.4.0-production",
        "uptime_seconds": uptime_seconds,
        "model": {
            "name": "Isolation Forest (Ensemble)",
            "n_estimators": 100,
            "features_count": len(FEATURES),
            "threshold": detector.threshold,
            "loaded": detector.is_loaded
        },
        "database": {
            "engine": analytics["storage_engine"],
            "total_logged": analytics["total_evaluations"],
            "fraud_count": analytics["fraud_count"]
        }
    })


# -------------------------------------------------------------
# Sample Presets Endpoint
# -------------------------------------------------------------
@app.route("/api/samples", methods=["GET"])
def get_samples():
    """Returns curated sample transactions for immediate 1-click testing."""
    return jsonify({
        "status": "success",
        "count": len(SAMPLE_PRESETS),
        "presets": SAMPLE_PRESETS
    })


# -------------------------------------------------------------
# Download Sample Test CSV
# -------------------------------------------------------------
@app.route("/api/sample-csv", methods=["GET"])
def download_sample_csv():
    """Downloads sample test CSV containing mixed legitimate and fraud transactions."""
    sample_csv_path = BASE_DIR / "test_data" / "mixed_batch_test_30.csv"
    if not sample_csv_path.exists():
        sample_csv_path = BASE_DIR / "data" / "sample_batch_test.csv"
    if sample_csv_path.exists():
        return send_file(
            sample_csv_path,
            as_attachment=True,
            download_name="sample_batch_transactions.csv",
            mimetype="text/csv"
        )
    return jsonify({"error": "Sample batch file not found on server."}), 404


# -------------------------------------------------------------
# Single Transaction Prediction Endpoint
# -------------------------------------------------------------
@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Evaluates a single transaction against the Isolation Forest defense model.
    Accepts JSON containing Time, V1-V28, and Amount.
    Returns anomaly score, threshold, risk percentage, risk tier, and feature breakdown.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                "status": "error",
                "error": "No JSON payload provided in request body."
            }), 400

        # Optional source tag ('manual', 'preset', 'simulator')
        source = data.pop("_source", "manual")

        # Run inference
        result = detector.predict_single(data)

        # Log transaction to database
        db_id = db.log_transaction(data, result, source=source)
        result["db_id"] = db_id
        result["timestamp"] = datetime.now().isoformat()

        return jsonify({
            "status": "success",
            **result
        })

    except ValueError as ve:
        return jsonify({
            "status": "error",
            "error": str(ve)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Internal inference error: {str(e)}"
        }), 500


# -------------------------------------------------------------
# Batch Prediction Endpoint (JSON Array or Multipart CSV)
# -------------------------------------------------------------
@app.route("/api/predict/batch", methods=["POST"])
def predict_batch():
    """
    Batch evaluation for high-throughput fraud audits.
    Supports:
    1. Direct JSON array: [{"Time": ..., "V1": ..., "Amount": ...}, ...]
    2. Multipart CSV file upload ('file' field)
    """
    try:
        records = []
        filename = "batch_input.json"

        # Check for uploaded CSV file
        if "file" in request.files:
            file = request.files["file"]
            filename = file.filename or "upload.csv"
            if not filename.lower().endswith(".csv"):
                return jsonify({"status": "error", "error": "Only CSV files are supported for file upload."}), 400

            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            df = pd.read_csv(stream)
            records = df.to_dict(orient="records")

        # Check for JSON array payload
        elif request.is_json:
            payload = request.get_json()
            if isinstance(payload, list):
                records = payload
            elif isinstance(payload, dict) and "transactions" in payload:
                records = payload["transactions"]

        if not records:
            return jsonify({
                "status": "error",
                "error": "No transactions found in request. Provide a JSON array or upload a CSV file."
            }), 400

        # Vectorized batch evaluation
        batch_summary = detector.predict_batch(records)

        # Log summary items to database
        db.log_batch(batch_summary["results"], source="batch_csv")

        return jsonify({
            "status": "success",
            "filename": filename,
            **batch_summary
        })

    except ValueError as ve:
        return jsonify({"status": "error", "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "error": f"Batch processing failed: {str(e)}"}), 500


# -------------------------------------------------------------
# History & Audit Log Endpoints
# -------------------------------------------------------------
@app.route("/api/history", methods=["GET"])
def get_history():
    """Returns paginated audit trail of evaluated transactions."""
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    verdict = request.args.get("verdict")

    records = db.get_history(limit=limit, offset=offset, verdict_filter=verdict)
    return jsonify({
        "status": "success",
        "count": len(records),
        "history": records
    })


@app.route("/api/history/clear", methods=["POST"])
def clear_history():
    """Wipes test transaction history log."""
    deleted = db.clear_history()
    return jsonify({
        "status": "success",
        "message": f"Cleared {deleted} transactions from database history."
    })


# -------------------------------------------------------------
# Analytics Endpoint
# -------------------------------------------------------------
@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    """Returns high-level platform intelligence and fraud distribution."""
    metrics = db.get_analytics()
    return jsonify({
        "status": "success",
        "analytics": metrics
    })


if __name__ == "__main__":
    print("=" * 65)
    print("      AEGIS RISKOPS // FRAUD DETECTION PLATFORM - BACKEND SERVER")
    print(f"      Threshold: {detector.threshold:.6f} | Models Loaded: {detector.is_loaded}")
    print(f"      Local Endpoint: http://127.0.0.1:5000")
    print("=" * 65)
    app.run(host="0.0.0.0", port=5000, debug=True)

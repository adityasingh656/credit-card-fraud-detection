# 🛡️ AEGIS RiskOps // Credit Card Fraud Detection Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/Backend-Flask%20REST%20API-black.svg)](https://flask.palletsprojects.com/)
[![Machine Learning](https://img.shields.io/badge/ML-Isolation%20Forest%20(scikit--learn)-orange.svg)](https://scikit-learn.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20MySQL-success.svg)](https://sqlite.org/)
[![UI Style](https://img.shields.io/badge/UI-Modern%20Fintech%20RiskOps-blue.svg)](#)

> **AEGIS RiskOps** is a high-throughput, enterprise-grade credit card fraud detection and risk intelligence platform powered by an **unsupervised Isolation Forest ensemble**. It delivers real-time transaction scoring, statistical feature variance explainability, batch CSV auditing, live streaming radar simulation, and persistent audit logging.

> 📄 **Academic & Enterprise Project Synopsis**: For the formal project specification, mathematical formulations, and evaluation metrics, see [`PROJECT_SYNOPSIS.md`](file:///c:/HCL%20project/Credit-Card%20Fraud%20detection/PROJECT_SYNOPSIS.md).

---

## 🚀 Key Highlights & Architectural Overview

```
                      ┌────────────────────────────────────────┐
                      │    AEGIS RiskOps Frontend Dashboard    │
                      │  (HTML5 / Modern CSS / ES6 / Chart.js) │
                      └──────────────────┬─────────────────────┘
                                         │ REST API / JSON
                                         ▼
                      ┌────────────────────────────────────────┐
                      │        Flask Enterprise Server         │
                      │          (backend/app.py)              │
                      └────┬───────────────────────────────┬───┘
                           │                               │
        ┌──────────────────▼────────────┐     ┌────────────▼──────────────────┐
        │     ML Inference Engine       │     │     Persistent Data Layer     │
        │    (backend/detector.py)      │     │     (backend/database.py)     │
        ├───────────────────────────────┤     ├───────────────────────────────┤
        │ • Isolation Forest Classifier │     │ • Local SQLite (Zero-config)  │
        │ • StandardScaler (Amount)     │     │ • Optional MySQL Auto-Sync    │
        │ • Threshold: 0.036042         │     │ • Audit Trail & Historical    │
        │ • PCA Feature Explainability  │     │   Risk Analytics              │
        └───────────────────────────────┘     └───────────────────────────────┘
```

---

## 🌟 Platform Capabilities

### 1. 🎯 Transaction Inspector
- **1-Click Benchmark Presets**: Instantly load verified real transactions (e.g. Card Skimming, Account Takeover, High Anomaly Outliers, or legitimate everyday retail purchases).
- **Dynamic Risk Gauge**: Animated circular SVG risk speedometer ($0\% - 100\%$) with seamless emerald $\rightarrow$ amber $\rightarrow$ crimson color morphing.
- **Statistical Feature Explainability**: Evaluates Z-score deviations across all 28 PCA features and transaction amount to highlight the specific indicators triggering an anomaly flag.
- **Audio Telemetry Feedback**: Synthesized Web Audio API sound alerts (harmonic chime for verified clean, alert pulse for detected threats).

### 2. 📁 Batch CSV Threat Auditor
- **Drag & Drop Dropzone**: Drop transaction CSV files directly onto the UI.
- **Vectorized High-Speed Processing**: Evaluates hundreds of transactions concurrently in milliseconds.
- **Interactive KPI Ribbon**: Live counters for total records, fraud count, clean count, flag incidence rate (%), and total dollar value at risk.
- **Filterable Data Grid**: Instant searching and 1-click filtering by verdict (`All`, `Flagged Fraud`, `Clean Pass`).
- **Export Capabilities**: 1-click export of flagged transactions to CSV or the complete audit dossier to JSON.
- **Sample File Generator**: Includes a downloadable 25-row test batch (`data/sample_batch_test.csv`) for zero-friction testing.

### 3. ⚡ Real-Time Live Stream Radar
- **Payment Ingestion Simulation**: Streams simulated card transactions with configurable velocities (1.2s, 0.6s, or 0.25s interval).
- **Radar Canvas**: Real-time rotating scan beam with live coordinate blip animations.
- **Automatic Interception**: Immediately blocks flagged anomalies, triggers audio-visual alarms, and tracks total prevented fraud loss in real time.

### 4. 📊 Audit Log & Analytics Terminal
- **Visual Analytics**: Interactive Chart.js anomaly score distribution vs. decision threshold, and doughnut charts for threat breakdown.
- **Database Persistence**: Automatic logging of transactions to embedded SQLite (`backend/fraud_records.db`) with support for MySQL.
- **Audit Table**: Full search and history review with pagination and clear-log operations.

---

## 🔬 Machine Learning Model Details

- **Algorithm**: `IsolationForest(n_estimators=100, random_state=42)`
- **Dataset**: European Cardholder Dataset ($284,807$ transactions, $492$ frauds — $0.172\%$ class imbalance).
- **Decision Threshold**: Locked at $\tau = 0.036042$, derived from validation set precision-recall curve optimization ($F_1$-score maximization).
- **Anomaly Score Formula**:
  $$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
  Where $h(x)$ is the path length in the isolation tree, and $c(n)$ is the average path length of unsuccessful searches in a Binary Search Tree.
- **Feature Scaling**: `StandardScaler` applied to `Amount` column to normalize skewed distribution.

---

## 🛠️ Quickstart & Execution

### 1. Requirements Installation
Ensure Python 3.10+ is installed:
```bash
pip install -r requirements.txt
```

### 2. Start the Flask Backend Server
```bash
python backend/app.py
```
Output:
```
=================================================================
      AEGIS RISKOPS // FRAUD DETECTION PLATFORM - BACKEND SERVER
      Threshold: 0.036042 | Models Loaded: True
      Local Endpoint: http://127.0.0.1:5000
=================================================================
```

Open your browser to:
👉 **`http://127.0.0.1:5000`**

*(Note: The frontend also features a **Zero-Setup Standalone Mode** — you can double-click [`frontend/index.html`](file:///c:/HCL%20project/Credit-Card%20Fraud%20detection/frontend/index.html) directly in any web browser and it will run using an integrated client-side scoring runtime!)*

---

### 3. CLI Prediction Tool
You can also run batch predictions directly from the command line:

```bash
# Evaluate a transaction CSV and save results to SQLite
python scripts/prediction.py data/sample_batch_test.csv

# Custom export destination
python scripts/prediction.py data/sample_batch_test.csv --export data/my_predictions.csv
```

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /api/status` | `GET` | Health check, model status, threshold, and DB stats. |
| `GET /api/samples` | `GET` | Returns 5 curated sample transactions (frauds & legitimate). |
| `GET /api/sample-csv` | `GET` | Direct download of sample test CSV for batch upload. |
| `POST /api/predict` | `POST` | Single transaction evaluation with anomaly score, risk %, and explainability. |
| `POST /api/predict/batch` | `POST` | Batch evaluation accepting JSON array or multipart CSV file. |
| `GET /api/history` | `GET` | Paginated audit trail of evaluated transactions (`?limit=50&verdict=FRAUD`). |
| `POST /api/history/clear`| `POST` | Wipes logged test history from database. |
| `GET /api/analytics` | `GET` | Aggregate stats: total volume, fraud volume, flag rate %. |

---

## 📂 Project Structure

```
Credit-Card Fraud detection/
├── backend/
│   ├── app.py                     # Modular Flask REST API application
│   ├── detector.py                # ML inference engine & feature explainability
│   ├── database.py                # Database persistence (SQLite default + MySQL sync)
│   ├── presets.py                 # Curated dataset presets for 1-click testing
│   └── fraud_records.db           # SQLite database (auto-created on first run)
├── frontend/
│   ├── index.html                 # Modern fintech RiskOps dashboard
│   ├── style.css                  # Dark slate fintech design system
│   └── script.js                  # Frontend controller, Chart.js, sound synth, simulator
├── test_data/
│   ├── confirmed_fraud_sample.csv # Confirmed fraud verification benchmark
│   ├── legitimate_normal_sample.csv # Verified clean shopping transactions
│   └── mixed_batch_test_30.csv    # 30-row mixed batch test file
├── models/
│   ├── final_isolation_forest.pkl # Active trained Isolation Forest model
│   ├── final_scaler.pkl           # Active StandardScaler artifact
│   └── fraud_threshold.pkl        # Optimal decision threshold (0.036042)
├── scripts/
│   └── prediction.py              # CLI batch evaluation script
├── notebooks/
│   ├── final_evaluation.ipynb     # Threshold tuning & test metrics
│   └── fraud_detection.ipynb      # Exploratory data analysis & model training
├── PROJECT_SYNOPSIS.docx          # Microsoft Word submission document
├── PROJECT_SYNOPSIS.md            # Formal project synopsis document (academic & enterprise)
├── requirements.txt               # Python package dependencies
└── README.md                      # Documentation & System Architecture
```

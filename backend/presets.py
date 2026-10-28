"""
Pre-configured sample transactions representing real-world legitimate,
suspicious, and confirmed fraud cases from the European credit card dataset.
Enables 1-click testing in both Frontend and API without needing to prepare CSVs.
"""

SAMPLE_PRESETS = [
    {
        "id": "fraud_card_skimming",
        "name": "🚨 Confirmed Fraud: Card Skimming Attack",
        "category": "FRAUD",
        "description": "Real fraudulent transaction (Index 543). Extreme negative V14 divergence (-4.29) and high V4 anomaly score (3.99).",
        "data": {
            "Time": 406.0,
            "Amount": 0.0,
            "V1": -2.3122265, "V2": 1.9519920, "V3": -1.6098507, "V4": 3.9979056,
            "V5": -0.5221879, "V6": -1.4265453, "V7": -2.5373873, "V8": 1.3916572,
            "V9": -2.7700893, "V10": -2.7722721, "V11": 3.2020332, "V12": -2.8999074,
            "V13": -0.5952219, "V14": -4.2892538, "V15": 0.3897241, "V16": -1.1407472,
            "V17": -2.8300557, "V18": -0.0168225, "V19": 0.4169557, "V20": 0.1269106,
            "V21": 0.5172324, "V22": -0.0350494, "V23": -0.4652111, "V24": 0.3201982,
            "V25": 0.0445192, "V26": 0.1778398, "V27": 0.2611450, "V28": -0.1432759
        }
    },
    {
        "id": "fraud_account_takeover",
        "name": "🚨 Confirmed Fraud: Account Takeover ($529)",
        "category": "FRAUD",
        "description": "High-value fraudulent purchase (Index 625). Heavy multi-feature PCA distortion with abnormal amount.",
        "data": {
            "Time": 472.0,
            "Amount": 529.0,
            "V1": -3.0435406, "V2": -3.1573071, "V3": 1.0884628, "V4": 2.2886436,
            "V5": 1.3598051, "V6": -1.0648225, "V7": 0.3255743, "V8": -0.0677937,
            "V9": -0.2709528, "V10": -0.8385866, "V11": -0.4145754, "V12": -0.5031409,
            "V13": 0.6765015, "V14": -1.6920289, "V15": 2.0006348, "V16": 0.6667797,
            "V17": 0.5997174, "V18": 1.7253210, "V19": 0.2833448, "V20": 2.1023388,
            "V21": 0.6616959, "V22": 0.4354772, "V23": 1.3759657, "V24": -0.2938032,
            "V25": 0.2797980, "V26": -0.1453617, "V27": -0.2527731, "V28": 0.0357642
        }
    },
    {
        "id": "fraud_known_anomaly",
        "name": "🚨 High Anomaly Outlier ($1,809.68)",
        "category": "FRAUD",
        "description": "Validated test vector (input_transaction.csv). Highly anomalous PCA profile (V5=-6.97, V12=-6.99) with anomaly score 0.0676.",
        "data": {
            "Time": 9064.0,
            "Amount": 1809.68,
            "V1": -3.4991075, "V2": 0.2585552, "V3": -4.4895581, "V4": 4.8538944,
            "V5": -6.9745215, "V6": 3.6283821, "V7": 5.4312709, "V8": -1.9467337,
            "V9": -0.7756801, "V10": -1.9877732, "V11": 4.6903957, "V12": -6.9980424,
            "V13": 1.4540120, "V14": -3.7380233, "V15": 0.3177421, "V16": -2.0135427,
            "V17": -5.1361351, "V18": -1.1838221, "V19": 1.6633940, "V20": -3.0426258,
            "V21": -1.0523683, "V22": 0.2048169, "V23": -2.1190074, "V24": 0.1702786,
            "V25": -0.3938441, "V26": 0.2963672, "V27": 1.9859132, "V28": -0.9004516
        }
    },
    {
        "id": "legit_retail_purchase",
        "name": "🛡️ Legitimate: Grocery Store POS ($149.62)",
        "category": "LEGITIMATE",
        "description": "Real legitimate purchase (Index 0). Regular shopping transaction with low PCA variation.",
        "data": {
            "Time": 0.0,
            "Amount": 149.62,
            "V1": -1.3598071, "V2": -0.0727812, "V3": 2.5363467, "V4": 1.3781552,
            "V5": -0.3383208, "V6": 0.4623878, "V7": 0.2395986, "V8": 0.0986979,
            "V9": 0.3637870, "V10": 0.0907942, "V11": -0.5515995, "V12": -0.6178009,
            "V13": -0.9913898, "V14": -0.3111694, "V15": 1.4681770, "V16": -0.4704005,
            "V17": 0.2079712, "V18": 0.0257906, "V19": 0.4039930, "V20": 0.2514121,
            "V21": -0.0183068, "V22": 0.2778376, "V23": -0.1104739, "V24": 0.0669281,
            "V25": 0.1285394, "V26": -0.1891148, "V27": 0.1335584, "V28": -0.0210531
        }
    },
    {
        "id": "legit_coffee_shop",
        "name": "🛡️ Legitimate: Coffee Shop ($2.69)",
        "category": "LEGITIMATE",
        "description": "Real everyday micro-transaction (Index 1). Typical contactless POS transaction with baseline scores.",
        "data": {
            "Time": 0.0,
            "Amount": 2.69,
            "V1": 1.1918571, "V2": 0.2661507, "V3": 0.1664801, "V4": 0.4481541,
            "V5": 0.0600176, "V6": -0.0823608, "V7": -0.0788030, "V8": 0.0851017,
            "V9": -0.2554251, "V10": -0.1669744, "V11": 1.6127267, "V12": 1.0652353,
            "V13": 0.4890950, "V14": -0.1437723, "V15": 0.6355581, "V16": 0.4639170,
            "V17": -0.1148047, "V18": -0.1833613, "V19": -0.1457830, "V20": -0.0690831,
            "V21": -0.2257752, "V22": -0.6386720, "V23": 0.1012880, "V24": -0.3398465,
            "V25": 0.1671704, "V26": 0.1258945, "V27": -0.0089831, "V28": 0.0147242
        }
    }
]

"""
predict.py

Loads a previously trained + saved model (isolation_forest.pkl,
robust_scaler.pkl) and scores NEW, unseen transaction data -- no
retraining involved. This is what you'd run in production once the
model is trained: new data comes in, gets scored, alerts come out.

Usage:
    python -m ml_engine.predict data/raw/new_unseen_transactions.csv
"""

import sys
import json
from pathlib import Path

from backend.ingestion import load_raw_dataset, CryptoDataIngestor
from ml_engine.feature_extractor import ForensicFeatureExtractor
from ml_engine.model import ForensicAnomalyDetector
from ml_engine.explainability import ForensicExplainer


def predict_on_new_data(new_data_path: Path, model_dir: Path, threshold: float = 50.0):
    # 1. Load + clean the new file exactly like training data was cleaned
    print(f"Loading new/unseen data: {new_data_path}")
    raw_df = load_raw_dataset(new_data_path)
    clean_df = CryptoDataIngestor().fit_transform(raw_df)
    print(f"Cleaned {len(clean_df):,} new transactions.")

    # 2. Extract the SAME 12 features used during training.
    #    Fresh extractor instance -- it's stateful (tracks wallet timing),
    #    so reusing the training-time one would leak training wallets'
    #    history into this new batch's velocity_score feature.
    extractor = ForensicFeatureExtractor()
    X_new = extractor.fit_transform(clean_df)

    # 3. Load the saved model -- NO retraining happens here
    print(f"Loading saved model from {model_dir} ...")
    detector = ForensicAnomalyDetector()
    detector.load(model_dir)  # restores model, scaler, and calibration bounds
    detector.feature_names_ = list(X_new.columns)

    # 4. Score every new transaction
    print("Scoring new transactions (no retraining)...")
    risk_scores = detector.predict_risk_scores(X_new)
    clean_df = clean_df.reset_index(drop=True)
    clean_df["risk_score"] = risk_scores
    clean_df["severity"] = [detector.classify_severity(s) for s in risk_scores]

    # 5. Generate ranked, explainable alerts for anything over threshold
    explainer = ForensicExplainer(detector.model, list(X_new.columns))
    ranked_alerts = explainer.generate_ranked_alerts(
        clean_df, X_new, risk_scores, threshold=threshold
    )

    print(f"\n{len(ranked_alerts)} of {len(clean_df)} new transactions flagged "
          f"(threshold={threshold}%)")

    return ranked_alerts, clean_df


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    model_dir = BASE_DIR / "model"

    # Accepts a file path as a command-line argument, or falls back to
    # a default test file if none given
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        BASE_DIR / "data" / "test" / "test.csv"

    alerts, scored_df = predict_on_new_data(input_path, model_dir, threshold=50.0)

    # Save results so the dashboard/anyone else can read them
    out_path = BASE_DIR / "ml_engine" / "outputs" / "new_data_alerts.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(alerts, f, indent=2)
    print(f"Saved {len(alerts)} alerts to {out_path}")

    if alerts:
        print("\n--- Top flagged transaction in new data ---")
        top = alerts[0]
        print(f"TXID: {top['txid']} | Risk: {top['risk_score']}%")
        print(top["evidence_card"]["forensic_narrative"])
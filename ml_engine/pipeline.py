from pathlib import Path
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# Imports from your modules
from backend.ingestion import load_raw_dataset, CryptoDataIngestor
from ml_engine.feature_extractor import ForensicFeatureExtractor
from ml_engine.model import ForensicAnomalyDetector
from ml_engine.explainability import ForensicExplainer
from ml_engine.evaluator import MLEvaluator


def ml_pipeline(
    data_path: Path,
    base_dir: Path,
    test_size: float = 0.20,
    threshold: float = 50.0,
):
    print("=" * 65)
    print("RIGOROUS BITCOIN FORENSIC ML BENCHMARK (TRAIN / TEST SPLIT)")
    print("=" * 65)

    # 1. Ingestion
    print(f"\n1. Loading raw dataset: {data_path}")
    raw_df = load_raw_dataset(data_path)
    clean_df = CryptoDataIngestor().fit_transform(raw_df)
    print(f"   Cleaned {len(clean_df):,} records.")

    has_labels = "is_anomaly" in clean_df.columns
    y_labels_full = (
        pd.to_numeric(clean_df["is_anomaly"], errors="coerce").fillna(0).astype(int).values
        if has_labels else np.zeros(len(clean_df))
    )

    # 2. SPLIT FIRST -- before any feature extraction happens.
    #    This is the key fix: ForensicFeatureExtractor is stateful
    #    (wallet_last_seen dict, used for velocity_score). Extracting
    #    features on the full dataset before splitting lets test-set
    #    transactions' timing features be influenced by wallets already
    #    "seen" in the training set -- a mild but real form of leakage.
    #    Splitting first and extracting separately per split closes that.
    #
    #    Stratified random split: guarantees train and test both get a
    #    representative share of the (rare, ~3%) anomalies. Without
    #    `stratify`, a random split could leave test with almost none,
    #    making evaluation meaningless.
    print(f"\n2. Splitting dataset ({int((1-test_size)*100)}% Train / {int(test_size*100)}% Test)...")

    train_idx, test_idx = train_test_split(
        np.arange(len(clean_df)),
        test_size=test_size,
        random_state=42,
        stratify=y_labels_full if has_labels else None,
    )

    # Keep each split internally sorted by time -- velocity_score needs
    # chronological order to compute meaningful gaps within each split.
    train_idx = np.sort(train_idx)
    test_idx = np.sort(test_idx)

    df_train = clean_df.iloc[train_idx].reset_index(drop=True)
    df_test = clean_df.iloc[test_idx].reset_index(drop=True)
    y_train = y_labels_full[train_idx]
    y_test = y_labels_full[test_idx]

    print(f"   - Train Set: {len(df_train):,} samples (Anomalies: {int(y_train.sum())})")
    print(f"   - Test Set:  {len(df_test):,} samples (Anomalies: {int(y_test.sum())}) [HELD OUT FOR EVALUATION]")

    # 3. Extract features SEPARATELY per split, with a FRESH extractor
    #    instance for each -- no shared wallet_last_seen state between them.
    print("\n3. Extracting 12D Forensic Features (separately per split)...")
    extractor_train = ForensicFeatureExtractor()
    X_train = extractor_train.fit_transform(df_train)

    extractor_test = ForensicFeatureExtractor()  # fresh state, doesn't know train's wallet history
    X_test = extractor_test.fit_transform(df_test)

    # 4. Fit Model ONLY on Training Data
    print("\n4. Training Isolation Forest ONLY on X_train...")
    detector = ForensicAnomalyDetector(contamination=0.03, n_estimators=200)
    detector.fit(X_train)

    model_dir = base_dir / "model"
    detector.save(model_dir)

    # 5. Predict on UNSEEN Test Data
    print("5. Predicting Calibrated Risk Scores on UNSEEN X_test...")
    test_risk_scores = detector.predict_risk_scores(X_test)
    df_test["risk_score"] = test_risk_scores

    # 6. Evaluate Model Performance on UNSEEN Test Data
    metrics = None
    if has_labels:
        print("\n6. Benchmarking Model on Test Set (Out-of-Sample Performance):")
        metrics = MLEvaluator.evaluate(y_test, test_risk_scores, threshold=threshold)

    # 7. Generate Explainability for Top Alerts in Test Set
    print("7. Generating SHAP Evidence for Top Flagged Leads in Test Set...")
    explainer = ForensicExplainer(detector.model, list(X_train.columns))
    ranked_alerts = explainer.generate_ranked_alerts(df_test, X_test, test_risk_scores, threshold=threshold)

    print(f"   Total Prioritized Leads Flagged in Test Set: {len(ranked_alerts)}")

    if ranked_alerts:
        print("\n--- Top Flagged Test Lead (Never Seen During Training) ---")
        top_alert = ranked_alerts[0]
        print(f"TXID: {top_alert['txid']} | Confidence: {top_alert['risk_score']}%")
        print(top_alert["evidence_card"]["forensic_narrative"])

    # 8. Persist full results so the dashboard / write-up has something
    #    to read after this script finishes -- previously nothing was saved.
    output_dir = base_dir / "ml_engine" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "alerts.json", "w") as f:
        json.dump(ranked_alerts, f, indent=2)
    print(f"\nSaved {len(ranked_alerts)} ranked alerts to {output_dir / 'alerts.json'}")

    if metrics is not None:
        with open(output_dir / "eval_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"Saved evaluation metrics to {output_dir / 'eval_metrics.json'}")

    return detector, ranked_alerts, metrics


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    dataset_file = BASE_DIR / "data" / "raw" / "synthetic_raw_data.csv"

    ml_pipeline(
        dataset_file,
        base_dir=BASE_DIR,
        test_size=0.20,
        threshold=50.0,
    )
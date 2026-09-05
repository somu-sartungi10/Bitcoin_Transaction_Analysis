import pandas as pd
from feature_engineering.step1_load_data import load_raw_csv
from feature_engineering.step2_clean_columns import clean_columns
from feature_engineering.step3_transaction_features import build_transaction_features


if __name__ == "__main__":
    raw_df = load_raw_csv("data/raw/cleaned_transactions_final.csv")
    clean_df = clean_columns(raw_df)
    txn_features = build_transaction_features(clean_df)

    # is_anomaly sirf validation ke liye use kar rahe hain, feature nahi hai
    txn_features["is_anomaly"] = clean_df["is_anomaly"]

    print("=== Normal vs Anomaly ke beech fark (mean values) ===")
    print(txn_features.groupby("is_anomaly")[[
        "input_count", "output_count", "fee_ratio",
        "max_to_min_output_ratio", "total_input_amount"
    ]].mean())

    print()
    print("=== Overall sanity check ===")
    print("Total rows:", len(txn_features))
    print("Anomaly count:", txn_features["is_anomaly"].sum())
    print("Infinity values check:", (txn_features.select_dtypes(include="number") == float("inf")).sum().sum())
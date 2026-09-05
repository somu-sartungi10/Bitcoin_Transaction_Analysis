import numpy as np
import pandas as pd
from ml_engine.feature_engineering.step1_load_data import load_raw_csv
from ml_engine.feature_engineering.step2_clean_columns import clean_columns


def build_transaction_features(df):
    """
    Ye function Bucket 1 ke 18 transaction-level features banata hai.
    Ye sirf ek row (ek transaction) ke andar ke data se ban jaate hain,
    kisi grouping/wallet ki zaroorat nahi.
    """
    feat = pd.DataFrame(index=df.index)

    in_amt = df["input_amounts_parsed"]
    out_amt = df["output_amounts_parsed"]
    in_addr = df["input_addresses_parsed"]
    out_addr = df["output_addresses_parsed"]

    # --- Transaction Structure (7 features) ---
    feat["input_count"] = in_addr.apply(len)
    feat["output_count"] = out_addr.apply(len)
    feat["total_input_amount"] = in_amt.apply(lambda l: sum(l) if l else 0.0)
    feat["total_output_amount"] = out_amt.apply(lambda l: sum(l) if l else 0.0)
    feat["input_output_ratio"] = feat["output_count"] / feat["input_count"].replace(0, np.nan)
    feat["amount_difference"] = feat["total_input_amount"] - feat["total_output_amount"]
    feat["output_amount_std"] = out_amt.apply(lambda l: np.std(l) if len(l) > 1 else 0.0)

    # --- Amount & Fee (7 features) ---
    feat["avg_input_amount"] = in_amt.apply(lambda l: np.mean(l) if l else 0.0)
    feat["avg_output_amount"] = out_amt.apply(lambda l: np.mean(l) if l else 0.0)
    feat["max_input_amount"] = in_amt.apply(lambda l: max(l) if l else 0.0)
    feat["max_output_amount"] = out_amt.apply(lambda l: max(l) if l else 0.0)
    feat["fee"] = df["fee"]
    feat["fee_ratio"] = feat["fee"] / feat["total_input_amount"].replace(0, np.nan)
    feat["max_to_min_output_ratio"] = out_amt.apply(
        lambda l: (max(l) / min(l)) if l and min(l) > 0 else np.nan
    )

    # --- Missing-input handling (jo humne decide kiya tha) ---
    # ratio-columns mein jo NaN hai (kyunki input hi nahi tha), unhe 0 se bhar do
    feat["input_output_ratio"] = feat["input_output_ratio"].fillna(0)
    feat["fee_ratio"] = feat["fee_ratio"].fillna(0)
    feat["max_to_min_output_ratio"] = feat["max_to_min_output_ratio"].fillna(0)

    # --- Script Type (one-hot encoding) ---
    script_dummies = pd.get_dummies(df["script_type"], prefix="script_type").astype(int)
    feat = pd.concat([feat, script_dummies], axis=1)

    # --- Time features (3) ---
    ts = pd.to_datetime(df["timestamp"], unit="s")
    feat["hour"] = ts.dt.hour
    feat["day_of_week"] = ts.dt.dayofweek
    feat["is_weekend"] = (feat["day_of_week"] >= 5).astype(int)

    return feat


if __name__ == "__main__":
    raw_df = load_raw_csv("data/raw/cleaned_transactions_final.csv")
    clean_df = clean_columns(raw_df)
    txn_features = build_transaction_features(clean_df)

    print("Total features banaye:", txn_features.shape[1])
    print()
    print("Feature names:")
    print(list(txn_features.columns))
    print()
    print("Koi NaN reh gaya kya check karo:")
    nan_counts = txn_features.isna().sum()
    print(nan_counts[nan_counts > 0] if nan_counts.sum() > 0 else "Koi NaN nahi hai - sab clean!")
    print()
    print("Pehli 3 rows:")
    print(txn_features.head(3))
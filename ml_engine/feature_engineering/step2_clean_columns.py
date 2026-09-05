import ast
import pandas as pd
from ml_engine.feature_engineering.step1_load_data import load_raw_csv


def safe_eval_list(x):
    """
    List jaise dikhne wale strings (jaise "[1.1649]") ko
    asli Python list mein convert karta hai.
    Agar convert nahi ho paaya, khaali list [] deta hai.
    """
    try:
        result = ast.literal_eval(x)
        return result if isinstance(result, list) else []
    except Exception:
        return []
def clean_columns(df):
    df = df.copy()

    df = df.drop(columns=[
        "input_amounts", "output_amounts",
        "input_addresses", "output_addresses",
    ])

    df = df.drop(columns=["dst_port"])

    df["input_amounts_parsed"] = df["input_amounts_parsed"].apply(safe_eval_list)
    df["output_amounts_parsed"] = df["output_amounts_parsed"].apply(safe_eval_list)
    df["input_addresses_parsed"] = df["input_addresses_parsed"].apply(safe_eval_list)
    df["output_addresses_parsed"] = df["output_addresses_parsed"].apply(safe_eval_list)

    # --- NAYI LINES: number-wale columns ko text se number banao ---
    df["timestamp"] = pd.to_numeric(df["timestamp"])
    df["src_port"] = pd.to_numeric(df["src_port"], errors="coerce")
    df["fee"] = pd.to_numeric(df["fee"])
    df["is_anomaly"] = pd.to_numeric(df["is_anomaly"]).astype(int)

    # --- NAYI LINES: True/False text ko asli boolean banao ---
    df["network_data_missing"] = df["network_data_missing"].map({"True": True, "False": False})
    df["input_data_missing"] = df["input_data_missing"].map({"True": True, "False": False})

    return df


if __name__ == "__main__":
    raw_df = load_raw_csv("data/raw/cleaned_transactions_final.csv")
    clean_df = clean_columns(raw_df)

    print("Pehle columns the:", len(raw_df.columns))
    print("Ab columns hain:", len(clean_df.columns))
    print()
    print("Baaki columns:")
    print(list(clean_df.columns))
    print()
    print("Check karo list-column sahi type mein hai:")
    print("Type of first input_amounts_parsed value:", type(clean_df["input_amounts_parsed"].iloc[0]))
    print("Value:", clean_df["input_amounts_parsed"].iloc[0])
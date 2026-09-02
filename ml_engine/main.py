from pathlib import Path
from backend.ingestion import load_raw_csv, CryptoDataIngestor

Base_dir = Path(__file__).resolve().parent.parent
raw_data_path = Base_dir / "data" / "raw" / "synthetic_btc_data.csv"

def run_test():
    print("ingesting dirty raw csv...")
    raw_df = load_raw_csv(raw_data_path)

    ingestor = CryptoDataIngestor()
    clean_df = ingestor.fit_transform(raw_df)

    print("ingestion complete")
    print(clean_df[['txid','src_ip', 'input_addresses', 'fee']].head())


if __name__ == "__main__":
    run_test()

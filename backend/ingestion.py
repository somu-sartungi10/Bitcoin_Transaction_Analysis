from pathlib import Path
import json
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

class CryptoDataIngestor(BaseEstimator, TransformerMixin):
    """
    Sanitizes, imputes, and validates raw Bitcoin blockchain
    and network layer transaction data.
    """

    def __init__(self):
        pass

    def fit(self, x, y=None):
        return self

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        df = x.copy()

        # 1. Network Layer Imputation
        df['src_ip'] = df['src_ip'].replace('', np.nan).fillna("0.0.0.0")
        df['dst_ip'] = df['dst_ip'].replace('', np.nan).fillna("0.0.0.0")
        
        # Source port unknown -> 0; Destination port default Bitcoin -> 8333
        df['src_port'] = pd.to_numeric(df['src_port'].replace('', np.nan), errors='coerce').fillna(0).astype(int)
        df['dst_port'] = pd.to_numeric(df['dst_port'].replace('', np.nan), errors='coerce').fillna(8333).astype(int)

        # 2. GeoIP / ASN fields (if present or missing)
        if 'geo_country' in df.columns:
            df['geo_country'] = df['geo_country'].replace('', np.nan).fillna("UNKNOWN")
        if 'asn' in df.columns:
            df['asn'] = df['asn'].replace('', np.nan).fillna("UNKNOWN_ASN")

        # 3. Bitcoin Protocol Tagging (Coinbase rewards)
        df['input_addresses'] = df['input_addresses'].replace('', np.nan).fillna("COINBASE_GENESIS")
        df['output_addresses'] = df['output_addresses'].replace('', np.nan).fillna("UNKNOWN_OUTPUT")
        df['input_amounts'] = df['input_amounts'].replace('', np.nan).fillna("0.0")
        df['output_amounts'] = df['output_amounts'].replace('', np.nan).fillna("0.0")

        # 4. Numeric & Timestamp Types
        df['fee'] = pd.to_numeric(df['fee'].replace('', np.nan), errors='coerce').fillna(0.0)
        df['timestamp'] = pd.to_numeric(df['timestamp'].replace('', np.nan), errors='coerce').fillna(0).astype(int)
        
        if 'script_type' in df.columns:
            df['script_type'] = df['script_type'].replace('', np.nan).fillna("unknown")

        return df


# --- Universal File Loaders (CSV, JSON, XML) ---

def load_raw_dataset(file_path: Path) -> pd.DataFrame:
    """
    Universal ingestion loader supporting CSV, JSON, and XML formats.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"❌ Dataset file not found at: {path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path, dtype=str)
    
    elif suffix == ".json":
        return pd.read_json(path, dtype=str)
    
    elif suffix == ".xml":
        # Parse XML root and records
        tree = ET.parse(path)
        root = tree.getroot()
        records = []
        for elem in root.findall("transaction") or root.findall("record"):
            row = {child.tag: child.text or "" for child in elem}
            records.append(row)
        return pd.DataFrame(records, dtype=str)
    
    else:
        raise ValueError(f"❌ Unsupported file format: {suffix}. Supported: .csv, .json, .xml")
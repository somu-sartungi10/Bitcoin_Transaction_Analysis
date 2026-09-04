import numpy as np
import pandas as pd
from typing import List, Dict, Any
from sklearn.base import BaseEstimator, TransformerMixin

class ForensicFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Scikit-Learn Transformer that extracts 12 domain-specific forensic features
    spanning blockchain flow, graph topology, and network timing.
    """

    # High-risk ASNs (Tor relays, bulletproof hosts, known illicit hosting)
    HIGH_RISK_ASNS = {"AS60729", "AS48282", "AS9009", "AS200052"}
    TOR_PORTS = {9050, 9051, 9150}

    def __init__(self):
        self.wallet_last_seen: Dict[str, int] = {}
        self.feature_names_: List[str] = [
            "num_inputs",
            "num_outputs",
            "fan_out_ratio",
            "total_in_amount",
            "total_out_amount",
            "dissipation_ratio",
            "output_entropy",
            "peeling_score",
            "is_high_risk_asn",
            "is_tor_port",
            "velocity_score",
            "structuring_score"
        ]

    def fit(self, X, y=None):
        return self

    def _calc_output_entropy(self, amounts: List[float]) -> float:
        """Computes Shannon Entropy to detect CoinJoin/Tumbler symmetry."""
        if not amounts or len(amounts) <= 1:
            return 0.0
        total = sum(amounts)
        if total <= 0:
            return 0.0
        probs = [amt / total for amt in amounts if amt > 0]
        if len(probs) <= 1:
            return 0.0
        return float(-sum(p * np.log2(p) for p in probs))

    def _calc_peeling_score(self, in_amts: List[float], out_amts: List[float]) -> float:
        """Detects 1-in-2-out peeling chains with a tiny peel and massive change hop."""
        if len(in_amts) == 1 and len(out_amts) == 2:
            total = sum(out_amts)
            if total > 0:
                min_r = min(out_amts) / total
                max_r = max(out_amts) / total
                if min_r <= 0.05 and max_r >= 0.94:
                    return 1.0
        return 0.0

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        features_list = []

        for _, row in X.iterrows():
            # 1. Parse address lists
            in_raw = str(row.get("input_addresses", ""))
            out_raw = str(row.get("output_addresses", ""))
            in_addrs = [a.strip() for a in in_raw.split(";") if a.strip() and a != "COINBASE_GENESIS"]
            out_addrs = [a.strip() for a in out_raw.split(";") if a.strip() and a != "UNKNOWN_OUTPUT"]

            # Parse amount lists safely
            def parse_amounts(val):
                if not val or pd.isna(val):
                    return []
                res = []
                for x in str(val).split(";"):
                    try:
                        res.append(float(x.strip()))
                    except ValueError:
                        continue
                return res

            in_amounts = parse_amounts(row.get("input_amounts", ""))
            out_amounts = parse_amounts(row.get("output_amounts", ""))

            num_in = len(in_addrs)
            num_out = len(out_addrs)
            total_in = sum(in_amounts) if in_amounts else 0.0
            total_out = sum(out_amounts) if out_amounts else 0.0

            # 2. Flow & Topology
            fan_out_ratio = num_out / (num_in + 1.0)
            fee = float(row.get("fee", 0.0)) if row.get("fee") and not pd.isna(row.get("fee")) else max(0.0, total_in - total_out)
            dissipation_ratio = fee / total_in if total_in > 0 else 0.0
            output_entropy = self._calc_output_entropy(out_amounts)
            peeling_score = self._calc_peeling_score(in_amounts, out_amounts)

            # 3. Network & ASN
            asn = str(row.get("asn", "")).strip()
            is_high_risk_asn = 1.0 if asn in self.HIGH_RISK_ASNS else 0.0

            src_port = row.get("src_port")
            try:
                port_num = int(src_port) if src_port and not pd.isna(src_port) else 0
            except ValueError:
                port_num = 0
            is_tor_port = 1.0 if port_num in self.TOR_PORTS else 0.0

            # 4. Temporal Velocity (Delta t)
            timestamp = int(row.get("timestamp", 0))
            min_delta = 3600.0
            for addr in in_addrs:
                if addr in self.wallet_last_seen:
                    delta = abs(timestamp - self.wallet_last_seen[addr])
                    if delta < min_delta:
                        min_delta = float(delta)
                self.wallet_last_seen[addr] = timestamp

            velocity_score = 1.0 / (1.0 + min_delta)

            # 5. Structuring / Smurfing (<0.5 BTC threshold proximity)
            structuring_score = 1.0 if (0.40 <= total_out <= 0.49 and num_out == 1) else 0.0

            features_list.append({
                "num_inputs": float(num_in),
                "num_outputs": float(num_out),
                "fan_out_ratio": float(fan_out_ratio),
                "total_in_amount": float(total_in),
                "total_out_amount": float(total_out),
                "dissipation_ratio": float(dissipation_ratio),
                "output_entropy": float(output_entropy),
                "peeling_score": float(peeling_score),
                "is_high_risk_asn": float(is_high_risk_asn),
                "is_tor_port": float(is_tor_port),
                "velocity_score": float(velocity_score),
                "structuring_score": float(structuring_score)
            })

        return pd.DataFrame(features_list, columns=self.feature_names_)
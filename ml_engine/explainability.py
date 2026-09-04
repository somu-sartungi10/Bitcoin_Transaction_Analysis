import shap
import pandas as pd
import numpy as np
from typing import Dict, List, Any

class ForensicExplainer:
    """
    SHAP Explainability Engine that transforms Isolation Forest tree path
    contributions into human-readable, actionable forensic evidence cards.
    """

    # Human-readable forensic interpretations for every feature
    FEATURE_DESCRIPTIONS = {
        "output_entropy": "Symmetric output amount distribution (CoinJoin / Tumbler signature)",
        "fan_out_ratio": "Abnormal 1-to-N fund dispersion ratio (Ransomware cash-out / Smurfing)",
        "peeling_score": "Classic Peeling Chain topology (Tiny payment + bulk change hop)",
        "is_high_risk_asn": "Broadcast originating from Tor Exit Relay or Bulletproof ASN",
        "velocity_score": "Automated high-frequency propagation burst (< 10 seconds)",
        "structuring_score": "Structuring / Smurfing threshold proximity (< 0.5 BTC split)",
        "dissipation_ratio": "Unusually high transaction fee dissipation percentage",
        "num_outputs": "Excessive count of destination receiving addresses",
        "num_inputs": "Multi-party input consolidation",
        "is_tor_port": "Traffic routed over Tor SOCKS proxy port (9050/9051)",
        "total_in_amount": "Abnormal transaction input volume",
        "total_out_amount": "Abnormal transaction output volume"
    }

    def __init__(self, detector_model, feature_names: List[str]):
        """
        :param detector_model: Trained IsolationForest instance
        :param feature_names: List of the 12 feature column names
        """
        self.model = detector_model
        self.feature_names = feature_names
        # TreeExplainer calculates exact Shapley values for tree ensembles
        self.explainer = shap.TreeExplainer(self.model)

    def explain_transaction(self, feature_row: pd.Series, risk_score: float) -> Dict[str, Any]:
        """
        Generates an individual forensic evidence card for a single flagged transaction.
        """
        # Ensure row is formatted as a 1-row DataFrame
        X_df = pd.DataFrame([feature_row], columns=self.feature_names)
        
        # Calculate raw SHAP values
        raw_shap = self.explainer.shap_values(X_df)[0]

        # In Isolation Forest, negative SHAP pushes towards shorter path (anomalous leaf).
        # We negate it so positive impact = features that increased the risk.
        anomaly_contributions = -raw_shap

        feature_impacts = []
        for feat_name, impact in zip(self.feature_names, anomaly_contributions):
            val = float(feature_row[feat_name])
            # Only include features that actively contributed to the anomalous decision
            if impact > 0.005 and val > 0:
                feature_impacts.append({
                    "feature": feat_name,
                    "observed_value": val,
                    "attribution_weight": round(float(impact), 4),
                    "description": self.FEATURE_DESCRIPTIONS.get(feat_name, feat_name)
                })

        # Sort features from highest impact to lowest
        feature_impacts.sort(key=lambda x: x["attribution_weight"], reverse=True)

        # Severity Classification
        if risk_score >= 90.0:
            severity = "CRITICAL"
        elif risk_score >= 75.0:
            severity = "HIGH"
        elif risk_score >= 50.0:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # Construct Natural Language Narrative
        top_reasons = [
            f"• {item['description']} (Observed: {item['observed_value']}, Attribution: +{item['attribution_weight']:.3f})"
            for item in feature_impacts[:3]
        ]
        
        if not top_reasons:
            narrative = f"Transaction flagged as {severity} Risk ({risk_score}% Confidence) due to multi-feature distance deviation."
        else:
            narrative = (
                f"Flagged as {severity} Risk ({risk_score}% Confidence)\n"
                f"Primary Forensic Indicators:\n" + "\n".join(top_reasons)
            )

        return {
            "risk_score": risk_score,
            "severity": severity,
            "top_features": feature_impacts[:5],
            "forensic_narrative": narrative
        }

    def generate_ranked_alerts(self, clean_df: pd.DataFrame, X_features: pd.DataFrame, 
                               risk_scores: np.ndarray, threshold: float = 75.0) -> List[Dict[str, Any]]:
        """
        Scans all transactions, filters by threshold, and returns a prioritized,
        explainable alert queue sorted from highest risk to lowest.
        """
        # Find all indices with risk >= threshold
        flagged_indices = np.where(risk_scores >= threshold)[0]
        
        # Sort descending by risk score
        sorted_indices = flagged_indices[np.argsort(-risk_scores[flagged_indices])]

        alerts = []
        for rank, idx in enumerate(sorted_indices, 1):
            tx_row = clean_df.iloc[idx]
            feat_row = X_features.iloc[idx]
            score = float(risk_scores[idx])

            evidence = self.explain_transaction(feat_row, score)

            alerts.append({
                "rank": rank,
                "txid": tx_row.get("txid", "N/A"),
                "timestamp": int(tx_row.get("timestamp", 0)),
                "src_ip": tx_row.get("src_ip", "0.0.0.0"),
                "geo_country": tx_row.get("geo_country", "UNKNOWN"),
                "asn": tx_row.get("asn", "UNKNOWN_ASN"),
                "risk_score": score,
                "severity": evidence["severity"],
                "evidence_card": evidence
            })

        return alerts
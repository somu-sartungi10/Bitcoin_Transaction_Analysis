import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
import joblib
from pathlib import Path
from typing import Tuple, List, Optional

class ForensicAnomalyDetector:
    """
    Unsupervised Anomaly Detection Engine for Bitcoin transactions.
    Combines Robust Scaling with an Isolation Forest ensemble and converts
    raw tree isolation depths into a Calibrated Forensic Risk Score (0-100%).
    """

    def __init__(self, contamination: float = 0.03, n_estimators: int = 200, random_state: int = 42):
        """
        :param contamination: Expected proportion of illicit/anomalous transactions (default: 3%)
        :param n_estimators: Number of Isolation Trees in the ensemble
        :param random_state: Seed for reproducible results
        """
        self.scaler = RobustScaler()
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            max_samples="auto",
            random_state=random_state,
            n_jobs=-1  # Use all CPU cores for fast training
        )
        self.is_fitted = False
        self.feature_names_: List[str] = []
        self._min_raw_score: Optional[float] = None
        self._max_raw_score: Optional[float] = None
 
    def fit(self, X: pd.DataFrame):
        """
        Fits the RobustScaler and Isolation Forest on the extracted feature matrix X.
        """
        self.feature_names_ = list(X.columns)
        
        # 1. Scale features robustly
        X_scaled = self.scaler.fit_transform(X)
        
        # 2. Train the Isolation Forest ensemble
        self.model.fit(X_scaled)
        
        # 3. Calculate score boundaries for calibration
        raw_scores = self.model.score_samples(X_scaled)
        self._min_raw_score = float(raw_scores.min())
        self._max_raw_score = float(raw_scores.max())
        self.is_fitted = True
        
        print(f"✅ Trained Isolation Forest ({self.model.n_estimators} trees) on {len(X):,} transactions.")
        return self

    def predict_risk_scores(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transforms raw tree decision scores into a calibrated 0.0% - 100.0% Forensic Risk Score.
        Higher score = higher probability of money laundering / illicit pattern.
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before running predictions!")

        X_scaled = self.scaler.transform(X)
        raw_scores = self.model.score_samples(X_scaled)

        # score_samples() returns negative values: lower score = more anomalous.
        # We invert it: (max - raw) / (max - min) so higher score = higher risk.
        spread = self._max_raw_score - self._min_raw_score
        if spread > 0:
            norm_scores = (self._max_raw_score - raw_scores) / spread
        else:
            norm_scores = np.zeros_like(raw_scores)

        # Clip bounds to [0.0, 1.0] and convert to percentage
        norm_scores = np.clip(norm_scores, 0.0, 1.0)
        return np.round(norm_scores * 100.0, 2)

    def classify_severity(self, risk_score: float) -> str:
        """
        Categorizes risk score into prioritized forensic alert tiers.
        """
        if risk_score >= 90.0:
            return "CRITICAL"
        elif risk_score >= 75.0:
            return "HIGH"
        elif risk_score >= 50.0:
            return "MEDIUM"
        return "LOW"

    def save(self, output_dir: Path):
        """Saves trained model and scaler weights to disk for offline use."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, output_dir / "isolation_forest.pkl")
        joblib.dump(self.scaler, output_dir / "robust_scaler.pkl")

        calibration ={
            "min_raw_score":self._min_raw_score,
            "max_raw_score":self._max_raw_score,
        }

        joblib.dump(calibration,output_dir/"score_calibration.pkl")
        print(f"💾 Saved model artifacts to: {output_dir}")

    def load(self, model_dir: Path):
        """Loads pre-trained model and scaler weights from disk."""
        model_dir = Path(model_dir)

        self.model = joblib.load(model_dir / "isolation_forest.pkl")

        self.scaler = joblib.load(model_dir / "robust_scaler.pkl")

        calibration = joblib.load(
            model_dir /"score_calibration.pkl"
        )

        self._min_raw_score = calibration['min_raw_score']
        self._max_raw_score=calibration['max_raw_score']

        self.is_fitted = True
        print(f"📂 Loaded model artifacts from: {model_dir}")
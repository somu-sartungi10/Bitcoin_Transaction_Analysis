import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix
)
from typing import Dict, Any

class MLEvaluator:
    """
    Evaluates ML anomaly detection performance against benchmark labels.
    """

    @staticmethod
    def evaluate(y_true: np.ndarray, risk_scores: np.ndarray, threshold: float = 75.0) -> Dict[str, Any]:
        """
        Computes Precision, Recall, F1-Score, ROC-AUC, PR-AUC, and Confusion Matrix.
        """
        # Convert continuous risk score (0-100%) to binary prediction (1 if score >= threshold)
        y_pred = (risk_scores >= threshold).astype(int)

        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        # Calculate Area Under ROC & PR curves (normalized to 0.0-1.0)
        norm_scores = risk_scores / 100.0
        try:
            roc_auc = roc_auc_score(y_true, norm_scores)
            pr_auc = average_precision_score(y_true, norm_scores)
        except ValueError:
            roc_auc, pr_auc = 0.0, 0.0

        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        
        false_positive_rate = (fp / (fp + tn)) * 100.0 if (fp + tn) > 0 else 0.0

        # Print formatted scorecard
        print("\n" + "=" * 65)
        print("🎯 FORENSIC ML BENCHMARK EVALUATION SCORECARD")
        print("=" * 65)
        print(f"• Total Evaluated Transactions: {len(y_true):,}")
        print(f"• Total Actual Anomalies:       {int(y_true.sum()):,}")
        print(f"• Total Flagged Leads (>= {threshold}%): {int(y_pred.sum()):,}")
        print("-" * 65)
        print(f"🏆 Detection Recall (Sensitivity): {recall * 100:.2f}%  (Caught {tp}/{tp+fn} anomalies)")
        print(f"🎯 Precision (Accuracy of Leads):  {precision * 100:.2f}%  ({tp}/{tp+fp} flags were true)")
        print(f"⚖️ F1-Score:                       {f1:.4f}")
        print(f"📈 ROC-AUC Score:                  {roc_auc:.4f}")
        print(f"📊 PR-AUC (Average Precision):     {pr_auc:.4f}")
        print(f"🛡️ False Positive Rate (FPR):      {false_positive_rate:.2f}%")
        print("-" * 65)
        print("🔍 Confusion Matrix:")
        print(f"   [True Normal (TN):  {tn:<6} | False Positive (FP): {fp:<6}]")
        print(f"   [False Negative (FN):{fn:<6} | True Positive (TP):   {tp:<6}]")
        print("=" * 65 + "\n")

        return {
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "roc_auc": float(roc_auc),
            "pr_auc": float(pr_auc),
            "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
        }
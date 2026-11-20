"""
KAIROS-TWIN Phase 4: Evaluation.

Comprehensive metrics for binary classification:
- ROC-AUC, PR-AUC
- Accuracy, Precision, Recall, F1
- Brier Score
- Confusion Matrix
"""
from __future__ import annotations
from typing import Dict, Tuple, Any
import numpy as np
from sklearn.metrics import (
    roc_auc_score, auc, precision_recall_curve,
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, brier_score_loss, roc_curve
)


class Evaluator:
    """Evaluate binary classification models."""

    @staticmethod
    def compute_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Compute comprehensive metric suite.

        Args:
            y_true: True binary labels
            y_pred: Predicted binary labels (from model.predict())
            y_proba: Predicted probabilities (from model.predict_proba()[:, 1])
            threshold: Decision threshold for binary prediction

        Returns:
            Dict with all metrics
        """
        # Ensure proper shapes and types
        y_true = np.asarray(y_true, dtype=bool)
        y_proba = np.asarray(y_proba, dtype=np.float32).ravel()

        # Recompute predictions using specified threshold
        y_pred_thresh = (y_proba >= threshold).astype(int)

        # Ranking metrics (threshold-invariant)
        roc_auc = roc_auc_score(y_true, y_proba)
        precision_curve, recall_curve, _ = precision_recall_curve(y_true, y_proba)
        pr_auc = auc(recall_curve, precision_curve)

        # Classification metrics (threshold-dependent)
        accuracy = accuracy_score(y_true, y_pred_thresh)
        precision = precision_score(y_true, y_pred_thresh, zero_division=0)
        recall = recall_score(y_true, y_pred_thresh, zero_division=0)
        f1 = f1_score(y_true, y_pred_thresh, zero_division=0)

        # Calibration
        brier = brier_score_loss(y_true, y_proba)

        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred_thresh).ravel()

        # ROC curve
        fpr, tpr, roc_thresholds = roc_curve(y_true, y_proba)

        return {
            'roc_auc': float(roc_auc),
            'pr_auc': float(pr_auc),
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'sensitivity': float(recall),  # Same as recall
            'specificity': float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0,
            'f1': float(f1),
            'brier_score': float(brier),
            'threshold': float(threshold),
            'confusion_matrix': {
                'tn': int(tn),
                'fp': int(fp),
                'fn': int(fn),
                'tp': int(tp),
            },
            'roc_curve': {
                'fpr': fpr.tolist(),
                'tpr': tpr.tolist(),
            },
            'pr_curve': {
                'precision': precision_curve.tolist(),
                'recall': recall_curve.tolist(),
            },
            'sample_count': len(y_true),
            'positive_count': int(y_true.sum()),
            'negative_count': int((~y_true).sum()),
        }

    @staticmethod
    def find_optimal_threshold(
        y_true: np.ndarray,
        y_proba: np.ndarray,
        metric: str = 'f1'
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Find optimal decision threshold on validation data.

        Args:
            y_true: True labels
            y_proba: Predicted probabilities
            metric: Metric to optimize ('f1', 'roc_auc', 'balanced_accuracy')

        Returns:
            (optimal_threshold, metrics_at_threshold)
        """
        y_true = np.asarray(y_true, dtype=bool)
        y_proba = np.asarray(y_proba, dtype=np.float32).ravel()

        thresholds = np.linspace(0.1, 0.9, 81)
        scores = []

        for thresh in thresholds:
            y_pred = (y_proba >= thresh).astype(int)

            if metric == 'f1':
                score = f1_score(y_true, y_pred, zero_division=0)
            elif metric == 'balanced_accuracy':
                tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
                sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
                specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
                score = (sensitivity + specificity) / 2
            elif metric == 'roc_auc':
                score = roc_auc_score(y_true, y_proba)  # Same for all thresholds
            else:
                raise ValueError(f"Unknown metric: {metric}")

            scores.append(score)

        best_idx = np.argmax(scores)
        best_threshold = thresholds[best_idx]
        best_metrics = Evaluator.compute_metrics(y_true, None, y_proba, best_threshold)

        return best_threshold, best_metrics

    @staticmethod
    def generate_report(metrics: Dict[str, Any]) -> str:
        """Generate markdown report of metrics."""
        report = []
        report.append("## Evaluation Metrics\n")

        report.append("### Ranking Metrics (Threshold-Invariant)")
        report.append(f"- ROC-AUC: {metrics['roc_auc']:.4f}")
        report.append(f"- PR-AUC: {metrics['pr_auc']:.4f}\n")

        report.append("### Classification Metrics (Threshold = {:.2f})".format(metrics['threshold']))
        report.append(f"- Accuracy: {metrics['accuracy']:.4f}")
        report.append(f"- Precision: {metrics['precision']:.4f}")
        report.append(f"- Recall (Sensitivity): {metrics['recall']:.4f}")
        report.append(f"- Specificity: {metrics['specificity']:.4f}")
        report.append(f"- F1-Score: {metrics['f1']:.4f}")
        report.append(f"- Brier Score: {metrics['brier_score']:.4f}\n")

        cm = metrics['confusion_matrix']
        report.append("### Confusion Matrix")
        report.append(f"```")
        report.append(f"                 Predicted")
        report.append(f"             Negative  Positive")
        report.append(f"Actual Neg   {cm['tn']:>6}    {cm['fp']:>6}")
        report.append(f"       Pos   {cm['fn']:>6}    {cm['tp']:>6}")
        report.append(f"```\n")

        report.append("### Sample Distribution")
        report.append(f"- Total samples: {metrics['sample_count']:,}")
        report.append(f"- Positive: {metrics['positive_count']:,} ({100*metrics['positive_count']/metrics['sample_count']:.1f}%)")
        report.append(f"- Negative: {metrics['negative_count']:,} ({100*metrics['negative_count']/metrics['sample_count']:.1f}%)\n")

        return '\n'.join(report)


def main():
    """Test evaluator."""
    from sklearn.datasets import make_classification

    # Generate toy data
    X, y = make_classification(n_samples=1000, n_features=46, n_informative=10, random_state=42)

    from sklearn.model_selection import train_test_split
    from ml.models import BaselineLogistic

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Train model
    model = BaselineLogistic(C=1.0)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    # Compute metrics
    metrics = Evaluator.compute_metrics(y_test, y_pred, y_proba, threshold=0.5)

    print("Evaluation test passed!")
    print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"PR-AUC: {metrics['pr_auc']:.4f}")
    print(f"F1: {metrics['f1']:.4f}")

    print("\n" + Evaluator.generate_report(metrics))

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

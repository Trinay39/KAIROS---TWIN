"""
KAIROS-TWIN Phase 4: Complete Validation Experiments.

Runs:
1. XGBoost training
2. Continuous regression (strain_index)
3. Feature-group ablation study
4. Calibration & interpretability analysis
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ml.data_loader import DataLoader
from ml.preprocessing import Preprocessor
from ml.models import BaselineLogistic, BaselineRandomForest, BaselineXGBoost
from ml.train import ModelTrainer
from ml.evaluate import Evaluator
from ml.calibration import CalibrationAnalyzer
from ml.interpretability import FeatureImportance


def run_xgboost_experiment():
    """Train XGBoost model with same protocol."""
    print("\n" + "=" * 70)
    print("XGBOOST TRAINING")
    print("=" * 70)

    loader = DataLoader('data/phase3/train.csv', 'data/phase3/val.csv', 'data/phase3/test.csv', verbose=False)
    loader.load()
    loader.validate()

    X_train, y_train, _ = loader.get_X_y('train')
    X_val, y_val, _ = loader.get_X_y('val')
    X_test, y_test, _ = loader.get_X_y('test')

    preprocessor = Preprocessor()
    X_train = preprocessor.fit_transform(X_train)
    X_val = preprocessor.transform(X_val)
    X_test = preprocessor.transform(X_test)

    # Tune XGBoost
    trainer = ModelTrainer(random_state=42)
    xgb_params, xgb_cv = trainer.tune_xgboost(X_train, y_train)

    if not xgb_params:
        print("XGBoost tuning failed")
        return None

    # Train final model
    model_xgb = BaselineXGBoost(**xgb_params, random_state=42)
    model_xgb.fit(X_train, y_train)

    # Evaluate
    y_val_proba = model_xgb.predict_proba(X_val)[:, 1]
    y_test_proba = model_xgb.predict_proba(X_test)[:, 1]

    val_metrics = Evaluator.compute_metrics(y_val, None, y_val_proba, threshold=0.5)
    test_metrics = Evaluator.compute_metrics(y_test, None, y_test_proba, threshold=0.5)

    print(f"  Val ROC-AUC: {val_metrics['roc_auc']:.4f}")
    print(f"  Test ROC-AUC: {test_metrics['roc_auc']:.4f}, F1: {test_metrics['f1']:.4f}")

    # Save
    Path('experiments/results').mkdir(parents=True, exist_ok=True)
    with open('experiments/results/xgboost.pkl', 'wb') as f:
        import pickle
        pickle.dump(model_xgb, f)

    with open('experiments/results/xgboost/metrics.json', 'w') as f:
        json.dump({'val': val_metrics, 'test': test_metrics}, f, indent=2)

    return {'val': val_metrics, 'test': test_metrics}


def run_regression_experiment():
    """Train regression models on y_continuous (strain_index)."""
    print("\n" + "=" * 70)
    print("REGRESSION: CONTINUOUS STRAIN INDEX")
    print("=" * 70)

    loader = DataLoader('data/phase3/train.csv', 'data/phase3/val.csv', 'data/phase3/test.csv', verbose=False)
    loader.load()
    loader.validate()

    X_train, _, y_train_cont = loader.get_X_y('train')
    X_val, _, y_val_cont = loader.get_X_y('val')
    X_test, _, y_test_cont = loader.get_X_y('test')

    preprocessor = Preprocessor()
    X_train = preprocessor.fit_transform(X_train)
    X_val = preprocessor.transform(X_val)
    X_test = preprocessor.transform(X_test)

    results = []

    # Ridge Regression
    ridge = Ridge(alpha=1.0, random_state=42)
    ridge.fit(X_train, y_train_cont)
    y_ridge_val = ridge.predict(X_val)
    y_ridge_test = ridge.predict(X_test)

    ridge_metrics = {
        'model': 'Ridge',
        'val_mae': mean_absolute_error(y_val_cont, y_ridge_val),
        'val_rmse': np.sqrt(mean_squared_error(y_val_cont, y_ridge_val)),
        'val_r2': r2_score(y_val_cont, y_ridge_val),
        'test_mae': mean_absolute_error(y_test_cont, y_ridge_test),
        'test_rmse': np.sqrt(mean_squared_error(y_test_cont, y_ridge_test)),
        'test_r2': r2_score(y_test_cont, y_ridge_test),
    }
    results.append(ridge_metrics)
    print(f"  Ridge: Test R²={ridge_metrics['test_r2']:.4f}, RMSE={ridge_metrics['test_rmse']:.4f}")

    # RF Regressor
    rf_reg = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf_reg.fit(X_train, y_train_cont)
    y_rf_val = rf_reg.predict(X_val)
    y_rf_test = rf_reg.predict(X_test)

    rf_metrics = {
        'model': 'RandomForest',
        'val_mae': mean_absolute_error(y_val_cont, y_rf_val),
        'val_rmse': np.sqrt(mean_squared_error(y_val_cont, y_rf_val)),
        'val_r2': r2_score(y_val_cont, y_rf_val),
        'test_mae': mean_absolute_error(y_test_cont, y_rf_test),
        'test_rmse': np.sqrt(mean_squared_error(y_test_cont, y_rf_test)),
        'test_r2': r2_score(y_test_cont, y_rf_test),
    }
    results.append(rf_metrics)
    print(f"  RF: Test R²={rf_metrics['test_r2']:.4f}, RMSE={rf_metrics['test_rmse']:.4f}")

    # Save
    df_results = pd.DataFrame(results)
    df_results.to_csv('experiments/results/regression_results.csv', index=False)
    with open('experiments/results/regression_metrics.json', 'w') as f:
        json.dump({'results': results}, f, indent=2)

    return results


def run_ablation_study():
    """Ablation study: leave-one-feature-group-out."""
    print("\n" + "=" * 70)
    print("FEATURE-GROUP ABLATION STUDY")
    print("=" * 70)

    loader = DataLoader('data/phase3/train.csv', 'data/phase3/val.csv', 'data/phase3/test.csv', verbose=False)
    loader.load()
    loader.validate()
    feature_names = loader.get_features()

    X_train, y_train, _ = loader.get_X_y('train')
    X_val, y_val, _ = loader.get_X_y('val')
    X_test, y_test, _ = loader.get_X_y('test')

    preprocessor = Preprocessor()
    X_train = preprocessor.fit_transform(X_train)
    X_val = preprocessor.transform(X_val)
    X_test = preprocessor.transform(X_test)

    # Define feature groups
    feature_groups = {
        'Academic': [f for f in feature_names if any(x in f for x in ['attendance', 'grade', 'deadline', 'subject'])],
        'Behavioral': [f for f in feature_names if any(x in f for x in ['study', 'session', 'focus', 'distraction', 'procrastination', 'break'])],
        'Recovery': [f for f in feature_names if any(x in f for x in ['sleep', 'recovery', 'rest', 'debt'])],
        'Workload': [f for f in feature_names if any(x in f for x in ['pending', 'deadline_density', 'workload_pressure', 'submission', 'effort_study'])],
        'Engagement': [f for f in feature_names if any(x in f for x in ['platform', 'interaction', 'stress', 'confidence'])],
        'Temporal': [f for f in feature_names if any(x in f for x in ['week', 'day_of_week', 'midterm', 'exam', 'days_until'])],
        'Interaction': [f for f in feature_names if any(x in f for x in ['imbalance', 'urgency', 'coherence', 'coupling'])],
    }

    ablations = ['All', 'Without Academic', 'Without Behavioral', 'Without Recovery', 'Without Workload', 'Without Engagement', 'Without Temporal', 'Without Interaction']
    results = []

    for ablation in ablations:
        if ablation == 'All':
            mask = np.ones(X_train.shape[1], dtype=bool)
        else:
            group_to_remove = ablation.replace('Without ', '')
            group_indices = [i for i, f in enumerate(feature_names) if f in feature_groups.get(group_to_remove, [])]
            mask = np.ones(X_train.shape[1], dtype=bool)
            mask[group_indices] = False

        X_train_abl = X_train[:, mask]
        X_val_abl = X_val[:, mask]
        X_test_abl = X_test[:, mask]

        # Train RF
        rf = RandomForestRegressor(n_estimators=500, max_depth=20, min_samples_leaf=5, max_features='sqrt', random_state=42, n_jobs=-1)
        rf.fit(X_train_abl, y_train)

        y_val_proba = rf.predict_proba(X_val_abl)[:, 1] if hasattr(rf, 'predict_proba') else None
        y_test_proba = rf.predict_proba(X_test_abl)[:, 1] if hasattr(rf, 'predict_proba') else None

        # For classification: use base RF from models.py
        rf_clf = RandomForestRegressor(n_estimators=500, max_depth=20, min_samples_leaf=5, max_features='sqrt', random_state=42, n_jobs=-1)
        # Need to train proper classifier instead
        from sklearn.ensemble import RandomForestClassifier
        rf_clf = RandomForestClassifier(n_estimators=500, max_depth=20, min_samples_leaf=5, max_features='sqrt', random_state=42, n_jobs=-1)
        rf_clf.fit(X_train_abl, y_train)

        y_val_proba = rf_clf.predict_proba(X_val_abl)[:, 1]
        y_test_proba = rf_clf.predict_proba(X_test_abl)[:, 1]

        val_metrics = Evaluator.compute_metrics(y_val, None, y_val_proba, threshold=0.5)
        test_metrics = Evaluator.compute_metrics(y_test, None, y_test_proba, threshold=0.5)

        results.append({
            'ablation': ablation,
            'val_roc_auc': val_metrics['roc_auc'],
            'val_pr_auc': val_metrics['pr_auc'],
            'val_f1': val_metrics['f1'],
            'val_brier': val_metrics['brier_score'],
            'test_roc_auc': test_metrics['roc_auc'],
            'test_pr_auc': test_metrics['pr_auc'],
            'test_f1': test_metrics['f1'],
            'test_brier': test_metrics['brier_score'],
        })

        print(f"  {ablation:25} -> Test ROC-AUC: {test_metrics['roc_auc']:.4f}")

    df_results = pd.DataFrame(results)
    df_results.to_csv('experiments/results/ablation_results.csv', index=False)

    return results


def main():
    """Run all validation experiments."""
    print("\n" + "=" * 70)
    print("PHASE 4 VALIDATION: COMPLETE EXPERIMENTS")
    print("=" * 70)

    # Step 2: XGBoost
    xgb_results = run_xgboost_experiment()

    # Step 3: Regression
    regression_results = run_regression_experiment()

    # Step 4: Ablation
    ablation_results = run_ablation_study()

    print("\n" + "=" * 70)
    print("PHASE 4 VALIDATION COMPLETE")
    print("=" * 70)
    print(f"\n✓ XGBoost: {'Completed' if xgb_results else 'Skipped'}")
    print(f"✓ Regression: {len(regression_results)} models")
    print(f"✓ Ablation: {len(ablation_results)} experiments")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

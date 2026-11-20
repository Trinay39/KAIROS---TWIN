"""
KAIROS-TWIN Phase 3: Integration Tests.

End-to-end integration tests for Phase 3 pipeline:
- Load synthetic data
- Compute twin states
- Extract features
- Compute labels
- Run temporal sampling
- Verify leakage checks pass
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from core.twin_engine import TwinEngine
from core.feature_engine import FeatureEngine
from core.label_engine import LabelEngine
from core.temporal_sampler import TemporalSampler
from core.leakage_tests import LeakageTests


class TestIntegration:
    """Integration test suite for Phase 3 pipeline."""

    @pytest.fixture
    def mini_dataset(self):
        """Create a mini dataset with 5 students over 90 days for quick testing."""
        np.random.seed(42)
        rows = []
        for s in range(1, 6):
            student_id = str(s)
            for day in range(1, 91):
                rows.append({
                    'student_id': student_id,
                    'day': day,
                    'day_of_week': (day - 1) % 7,
                    'study_hours': max(0.0, np.random.normal(3.5, 1.2)),
                    'sleep_hours': max(3.0, np.random.normal(7.2, 1.0)),
                    'stress_level': np.clip(np.random.normal(0.4, 0.15), 0.1, 1.0),
                    'recovery_index': np.clip(np.random.normal(0.7, 0.1), 0.1, 1.0),
                    'engagement_score': np.clip(np.random.normal(0.6, 0.15), 0.1, 1.0),
                    'workload_pressure': np.clip(np.random.normal(0.4, 0.2), 0.1, 1.0),
                    'platform_interactions': int(np.random.poisson(15)),
                    'attendance_rate': np.clip(np.random.normal(0.9, 0.05), 0.0, 1.0),
                    'grade': np.clip(np.random.normal(72, 10), 0, 100),
                    'assignment_due_today': int(np.random.binomial(1, 0.15)),
                    'exam_due_today': int(np.random.binomial(1, 0.03)),
                    'pending_assignments': int(np.random.randint(0, 10)),
                    'upcoming_deadlines_7d': int(np.random.randint(0, 5)),
                    'missed_deadline_observed': int(np.random.binomial(1, 0.05)),
                })
        return pd.DataFrame(rows)

    def test_pipeline_end_to_end_mini(self, mini_dataset):
        """Test full end-to-end flow on mini dataset."""
        twin_engine = TwinEngine()
        feature_engine = FeatureEngine()
        label_engine = LabelEngine()
        sampler = TemporalSampler()
        leakage_tester = LeakageTests()

        students = sorted(mini_dataset['student_id'].unique())
        assert len(students) == 5

        # 1. Compute twin states
        twin_states = {}
        for student_id in students:
            student_df = mini_dataset[mini_dataset['student_id'] == student_id]
            for day in range(1, 91):
                obs = student_df[student_df['day'] <= day]
                state = twin_engine.compute_state(student_id, day, obs)
                twin_states[(student_id, day)] = state

        assert len(twin_states) == 5 * 90

        # 2. Extract features
        features = {}
        for (sid, d), state in twin_states.items():
            feat = feature_engine.extract_features(state)
            assert len(feat) == 46
            features[(sid, d)] = feat

        # 3. Compute labels
        labels = {}
        for student_id in students:
            student_df = mini_dataset[mini_dataset['student_id'] == student_id]
            for day in range(1, 84):
                outcome = student_df[(student_df['day'] > day) & (student_df['day'] <= day + 7)]
                lbl = label_engine.compute_labels(student_id, day, outcome)
                labels[(student_id, day)] = lbl

        assert len(labels) == 5 * 83

        # 4. Temporal sampling
        train_s, val_s, test_s = sampler.create_temporal_samples(features, labels, students)
        assert len(train_s) == 5 * (55 - 15 + 1)  # 41 days per student
        assert len(val_s) == 5 * (69 - 56 + 1)    # 14 days per student
        assert len(test_s) == 5 * (83 - 70 + 1)   # 14 days per student

        # 5. Leakage detection
        results = leakage_tester.run_all_tests(train_s, val_s, test_s)
        assert results['tests']['feature_temporal_bounds']['passed'] is True
        assert results['tests']['no_label_in_features']['passed'] is True
        assert results['tests']['samples_temporal_separation']['passed'] is True

        # 6. DataFrame conversion
        df_train = sampler.to_dataframe(train_s)
        df_val = sampler.to_dataframe(val_s)
        df_test = sampler.to_dataframe(test_s)

        assert df_train.shape[0] == len(train_s)
        assert df_val.shape[0] == len(val_s)
        assert df_test.shape[0] == len(test_s)

        # 46 feature columns + student_id + day + y_binary + y_continuous + split + criteria columns
        feature_cols = [c for c in df_train.columns if c.startswith('X_')]
        assert len(feature_cols) == 46


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

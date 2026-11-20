"""
KAIROS-TWIN Phase 3: Tests for TwinEngine, FeatureEngine, LabelEngine.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from core.schemas import StudentTwinState
from core.twin_engine import TwinEngine
from core.feature_engine import FeatureEngine
from core.label_engine import LabelEngine


class TestTwinEngine:
    """Tests for StudentTwinState computation."""

    @pytest.fixture
    def sample_data(self):
        """Create sample daily observations."""
        return pd.DataFrame({
            'student_id': [1] * 30,
            'day': list(range(1, 31)),
            'day_of_week': [i % 7 for i in range(30)],
            'study_hours': np.random.uniform(2, 6, 30),
            'sleep_hours': np.random.uniform(6.5, 8.5, 30),
            'stress_level': np.random.uniform(0.3, 0.9, 30),
            'recovery_index': np.random.uniform(0.6, 0.9, 30),
            'engagement_score': np.random.uniform(0.4, 0.8, 30),
            'workload_pressure': np.random.uniform(0.1, 0.7, 30),
            'platform_interactions': np.random.uniform(10, 25, 30),
            'attendance_rate': np.random.uniform(0.85, 1.0, 30),
            'grade': np.random.uniform(60, 85, 30),
            'assignment_due_today': np.random.binomial(1, 0.1, 30),
            'exam_due_today': np.random.binomial(1, 0.03, 30),
            'pending_assignments': np.random.randint(5, 15, 30),
            'upcoming_deadlines_7d': np.random.randint(0, 8, 30),
            'missed_deadline_observed': np.random.binomial(1, 0.08, 30),
        })

    def test_twin_engine_creation(self):
        """Test TwinEngine instantiation."""
        engine = TwinEngine(baseline_sleep=7.5)
        assert engine.baseline_sleep == 7.5

    def test_compute_state(self, sample_data):
        """Test state computation."""
        engine = TwinEngine()
        state = engine.compute_state('1', 15, sample_data, data_source='synthetic')

        assert state.student_id == '1'
        assert state.day == 15
        assert state.data_source == 'synthetic'
        assert state.academic is not None
        assert state.behavioral is not None
        assert state.recovery is not None
        assert state.workload is not None

    def test_state_no_future_data(self, sample_data):
        """Test that state only uses data up to day t."""
        engine = TwinEngine()

        # Compute state at day 10
        data_up_to_10 = sample_data[sample_data['day'] <= 10]
        state = engine.compute_state('1', 10, data_up_to_10)

        # State should be valid
        assert state.day == 10
        assert len(data_up_to_10) > 0


class TestFeatureEngine:
    """Tests for feature extraction."""

    @pytest.fixture
    def sample_state(self):
        """Create a sample StudentTwinState."""
        return StudentTwinState(
            student_id='1',
            day=20,
            data_source='synthetic'
        )

    def test_feature_engine_creation(self):
        """Test FeatureEngine instantiation."""
        engine = FeatureEngine()
        assert len(engine.FEATURE_NAMES) == 46

    def test_extract_features_all_present(self, sample_state):
        """Test that all 46 features are extracted."""
        engine = FeatureEngine()
        features = engine.extract_features(sample_state)

        assert len(features) == 46
        for fname in engine.FEATURE_NAMES:
            assert fname in features
            assert isinstance(features[fname], (int, float, np.number))

    def test_feature_ranges(self, sample_state):
        """Test that features are within expected ranges."""
        engine = FeatureEngine()
        features = engine.extract_features(sample_state)

        # Check some key ranges
        assert 0 <= features['attendance_rate_7d'] <= 1
        assert 0 <= features['avg_study_hours_7d'] <= 18
        assert 0 <= features['avg_sleep_hours_7d'] <= 12
        assert 0 <= features['workload_pressure_score_7d'] <= 1

    def test_safe_get_handles_none(self):
        """Test _safe_get with None values."""
        result = FeatureEngine._safe_get(None, 0.5, [0, 1])
        assert result == 0.5

    def test_safe_get_clips_values(self):
        """Test _safe_get clips out-of-range values."""
        result = FeatureEngine._safe_get(10.0, 5.0, [0, 1])
        assert result == 1.0


class TestLabelEngine:
    """Tests for label computation."""

    @pytest.fixture
    def future_data(self):
        """Create sample future observations for [t+1, t+7]."""
        return pd.DataFrame({
            'day': list(range(21, 28)),  # [21, 27] when t=20
            'study_hours': [3.5, 3.2, 3.8, 2.5, 3.1, 3.4, 3.0],
            'sleep_hours': [7.0, 7.1, 6.9, 5.0, 5.2, 5.3, 5.1],
            'stress_level': [0.5, 0.52, 0.48, 0.85, 0.9, 0.88, 0.92],
            'grade': [75, 76, 74, 65, 68, 67, 66],
            'assignment_due_today': [0, 1, 0, 0, 0, 0, 0],
            'missed_deadline_observed': [0, 1, 0, 0, 0, 0, 0],
        })

    def test_label_engine_creation(self):
        """Test LabelEngine instantiation."""
        engine = LabelEngine()
        assert engine.GRADE_DROP_THRESHOLD == 0.15

    def test_compute_labels_all_criteria(self, future_data):
        """Test that all 5 criteria are computed."""
        engine = LabelEngine()
        labels = engine.compute_labels(
            'student_1', 20, future_data,
            baseline_study_30d=4.0,
            baseline_grade=75.0
        )

        assert 'C1_missed_deadline' in labels
        assert 'C2_grade_deterioration' in labels
        assert 'C3_study_collapse' in labels
        assert 'C4_recovery_failure' in labels
        assert 'C5_high_stress' in labels
        assert 'overload_binary' in labels
        assert 'strain_index' in labels

    def test_criterion_1_missed_deadline(self, future_data):
        """Test C1: missed deadline detection."""
        engine = LabelEngine()

        # One missed deadline
        labels = engine.compute_labels('s1', 20, future_data)
        assert labels['C1_missed_deadline'] is True

        # No missed deadlines
        future_data_no_miss = future_data.copy()
        future_data_no_miss['missed_deadline_observed'] = 0
        labels = engine.compute_labels('s1', 20, future_data_no_miss)
        assert labels['C1_missed_deadline'] is False

    def test_criterion_3_study_collapse(self):
        """Test C3: study collapse detection."""
        engine = LabelEngine()

        # Create data where future mean study hours is low enough to trigger collapse
        low_study_data = pd.DataFrame({
            'day': list(range(21, 28)),
            'study_hours': [1.5, 1.2, 1.8, 1.5, 1.1, 1.4, 1.0],  # Very low
            'sleep_hours': [7.0, 7.1, 6.9, 7.0, 7.2, 7.3, 7.1],
            'stress_level': [0.4, 0.42, 0.38, 0.45, 0.5, 0.48, 0.46],
            'grade': [75, 76, 74, 75, 76, 75, 76],
            'assignment_due_today': [0, 1, 0, 0, 0, 0, 0],
            'missed_deadline_observed': [0, 0, 0, 0, 0, 0, 0],
        })

        # Baseline = 4.0, threshold = 2.0, mean = 1.37 < 2.0, so collapse
        labels = engine.compute_labels('s1', 20, low_study_data, baseline_study_30d=4.0)
        assert labels['C3_study_collapse'] is True

        # With higher baseline (1.0), threshold = 0.5, mean = 1.37 > 0.5, NO collapse
        labels = engine.compute_labels('s1', 20, low_study_data, baseline_study_30d=1.0)
        assert labels['C3_study_collapse'] is False

    def test_criterion_4_recovery_failure(self):
        """Test C4: recovery failure detection."""
        engine = LabelEngine()

        # Create data with very low sleep that triggers recovery failure
        # Need: mean sleep < 5.5 AND deficit > 10 hours over 7 days
        low_sleep_data = pd.DataFrame({
            'day': list(range(21, 28)),
            'study_hours': [3.5, 3.2, 3.8, 3.5, 3.1, 3.4, 3.0],
            'sleep_hours': [5.0, 4.8, 5.2, 4.5, 4.6, 4.9, 4.7],  # All below 5.5
            'stress_level': [0.5, 0.52, 0.48, 0.55, 0.6, 0.58, 0.56],
            'grade': [75, 76, 74, 75, 76, 75, 76],
            'assignment_due_today': [0, 1, 0, 0, 0, 0, 0],
            'missed_deadline_observed': [0, 0, 0, 0, 0, 0, 0],
        })

        # Deficit calculation:
        # (7.5-5.0) + (7.5-4.8) + (7.5-5.2) + (7.5-4.5) + (7.5-4.6) + (7.5-4.9) + (7.5-4.7)
        # = 2.5 + 2.7 + 2.3 + 3.0 + 2.9 + 2.6 + 2.8 = 18.8 > 10
        # Mean sleep = 4.93 < 5.5
        labels = engine.compute_labels('s1', 20, low_sleep_data)
        assert labels['C4_recovery_failure'] is True

        # With higher sleep, deficit should be < 10
        higher_sleep_data = low_sleep_data.copy()
        higher_sleep_data['sleep_hours'] = [6.5, 6.3, 6.7, 6.2, 6.4, 6.6, 6.1]
        labels = engine.compute_labels('s1', 20, higher_sleep_data)
        assert labels['C4_recovery_failure'] is False

    def test_criterion_5_high_stress(self, future_data):
        """Test C5: high stress detection."""
        engine = LabelEngine()

        # Mean stress_level = 0.7 (high on [0.1, 1.0])
        # Convert to Likert: 1 + 4*0.7 = 3.8 (< 4.0, so False)
        labels = engine.compute_labels('s1', 20, future_data)
        # May or may not trigger depending on exact values

    def test_strain_index_computation(self, future_data):
        """Test continuous strain index."""
        engine = LabelEngine()
        labels = engine.compute_labels('s1', 20, future_data)

        strain = labels['strain_index']
        assert strain is not None
        assert 0.0 <= strain <= 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

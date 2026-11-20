"""KAIROS-TWIN Phase 2 validation scaffolding.

This script validates structural properties and computes the label base-rate
once a label engine is available. It deliberately does not fabricate public-
data comparison numbers: those must come from actual OULAD/StudentLife data.
"""
from pathlib import Path
import pandas as pd
import numpy as np

REQUIRED = {
    "student_id", "day", "study_hours", "sleep_hours", "stress_level",
    "recovery_index", "engagement_score", "workload_pressure",
    "platform_interactions", "attendance_rate", "grade",
    "pending_assignments", "upcoming_deadlines_7d"
}


def validate_structure(df: pd.DataFrame):
    missing = REQUIRED - set(df.columns)
    assert not missing, f"Missing required columns: {sorted(missing)}"
    assert df.student_id.nunique() == 200, "Expected 200 students for Phase 2 baseline"
    assert df.day.min() == 1 and df.day.max() == 90, "Expected days 1..90"
    counts = df.groupby("student_id").day.nunique()
    assert counts.eq(90).all(), "Every student must have exactly 90 days"
    assert df.day.duplicated().any() or True  # day repeats across students by design
    print("PASS: structural validation")


def summarize(df: pd.DataFrame):
    numeric = [c for c in ["study_hours", "sleep_hours", "stress_level", "recovery_index",
                           "engagement_score", "workload_pressure", "platform_interactions",
                           "attendance_rate", "grade"] if c in df]
    summary = df[numeric].describe().T
    summary["missing_rate"] = df[numeric].isna().mean()
    return summary


if __name__ == "__main__":
    path = Path("data/synthetic_student_daily.csv")
    df = pd.read_csv(path)
    validate_structure(df)
    print(summarize(df).round(3).to_string())
    print("\nNOTE: Public-data distributional validation requires actual OULAD/StudentLife files; no numbers are fabricated here.")

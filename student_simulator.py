"""KAIROS-TWIN Phase 2: Synthetic student trajectory simulator.

Generates daily longitudinal observations for 200 students over 90 days.
The simulator is intentionally transparent/configurable so its assumptions can
be inspected and perturbed in Phase 9 robustness experiments.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import math
import numpy as np
import pandas as pd


@dataclass
class SimulatorConfig:
    n_students: int = 200
    n_days: int = 90
    seed: int = 42
    missing_rate: float = 0.15
    sleep_sensitivity: float = 0.50
    deadline_motivation: float = 0.35
    observation_noise: float = 0.10
    baseline_sleep: float = 7.5


class StudentSimulator:
    """Transparent latent-state simulator for academic workload research."""

    def __init__(self, config: SimulatorConfig | None = None):
        self.cfg = config or SimulatorConfig()
        self.rng = np.random.default_rng(self.cfg.seed)

    @staticmethod
    def _clip(x, lo, hi):
        return float(np.clip(x, lo, hi))

    def generate(self) -> pd.DataFrame:
        rows = []
        c = self.cfg

        for sid in range(1, c.n_students + 1):
            # Student-specific stable traits. These are latent generators, not labels.
            ability = self.rng.normal(0, 1)
            conscientiousness = self.rng.normal(0, 1)
            resilience = self.rng.normal(0, 1)
            baseline_study = self._clip(4.5 + 1.0 * ability + 0.6 * conscientiousness + self.rng.normal(0, .6), 1.0, 9.0)
            baseline_stress = self._clip(0.45 - .08 * resilience + self.rng.normal(0, .05), .05, .90)

            stress = baseline_stress
            sleep = c.baseline_sleep + .3 * resilience
            study = baseline_study
            recovery = .7 + .1 * resilience
            engagement = .65 + .08 * conscientiousness
            prior_grade = self._clip(70 + 8 * ability + 5 * conscientiousness + self.rng.normal(0, 5), 40, 95)

            # Semester assessment/deadline process.
            assignment_due = set()
            exam_due = set()
            for d in range(1, c.n_days + 1):
                if self.rng.random() < .13:
                    assignment_due.add(d)
                if d >= 10 and self.rng.random() < .035:
                    exam_due.add(d)

            daily_study = []
            daily_sleep = []
            daily_stress = []
            daily_engagement = []
            daily_workload = []
            daily_grade = []

            for day in range(1, c.n_days + 1):
                dow = (day - 1) % 7
                upcoming_assignments = sum(1 for x in assignment_due if day <= x <= day + 6)
                upcoming_exams = sum(1 for x in exam_due if day <= x <= day + 6)
                due_today = int(day in assignment_due) + int(day in exam_due)
                workload = self._clip(.18 * upcoming_assignments + .38 * upcoming_exams + .22 * due_today + self.rng.normal(0, .06), 0, 1)

                deadline_effect = self.cfg.deadline_motivation * min(upcoming_assignments / 4, 1)
                study_target = baseline_study + deadline_effect * 2.0 - .9 * stress - .7 * workload
                study = self._clip(.70 * study + .30 * study_target + self.rng.normal(0, c.observation_noise), .1, 12)

                stress_target = baseline_stress + .62 * workload + .16 * max(0, 5.5 - study) - .10 * resilience
                stress = self._clip(.78 * stress + .22 * stress_target + self.rng.normal(0, .04), 0, 1)

                sleep_target = c.baseline_sleep - c.sleep_sensitivity * stress - .08 * max(0, study - 6)
                sleep = self._clip(.82 * sleep + .18 * sleep_target + self.rng.normal(0, c.observation_noise), 4, 10)

                recovery = self._clip(.55 * recovery + .45 * (sleep / c.baseline_sleep) - .12 * stress, 0, 1.2)
                engagement = self._clip(.78 * engagement + .22 * (0.65 + .15 * conscientiousness - .20 * stress + .10 * recovery) + self.rng.normal(0, .03), 0, 1)

                # Grade is a slowly changing academic outcome, intentionally noisy.
                grade_target = prior_grade + .8 * ability + .5 * conscientiousness - .8 * stress - .15 * workload
                grade = self._clip(.94 * prior_grade + .06 * grade_target + self.rng.normal(0, 1.5), 0, 100)
                prior_grade = grade

                # Simple observable/proxy signals.
                platform = self._clip(12 + 3.5 * engagement + 1.2 * study - 3 * stress + self.rng.normal(0, 1.8), 0, 40)
                attendance = self._clip(.95 - .08 * stress - .03 * workload + self.rng.normal(0, .025), .4, 1)
                missed_deadline = int(day in assignment_due and (stress + workload - .25 * resilience) > .72)

                rows.append({
                    "student_id": sid,
                    "day": day,
                    "day_of_week": dow,
                    "study_hours": study,
                    "sleep_hours": sleep,
                    "stress_level": stress,
                    "recovery_index": recovery,
                    "engagement_score": engagement,
                    "workload_pressure": workload,
                    "platform_interactions": platform,
                    "attendance_rate": attendance,
                    "grade": grade,
                    "assignment_due_today": int(day in assignment_due),
                    "exam_due_today": int(day in exam_due),
                    "pending_assignments": sum(1 for x in assignment_due if x >= day),
                    "upcoming_deadlines_7d": upcoming_assignments + upcoming_exams,
                    "missed_deadline_observed": missed_deadline,
                })

        df = pd.DataFrame(rows)

        # Add missingness only to observed measurements, never identifiers/labels.
        observed = ["study_hours", "sleep_hours", "stress_level", "recovery_index",
                    "engagement_score", "workload_pressure", "platform_interactions",
                    "attendance_rate", "grade"]
        mask = self.rng.random((len(df), len(observed))) < c.missing_rate
        for j, col in enumerate(observed):
            df.loc[mask[:, j], col] = np.nan

        return df


if __name__ == "__main__":
    cfg = SimulatorConfig()
    sim = StudentSimulator(cfg)
    df = sim.generate()
    out = Path("data")
    out.mkdir(exist_ok=True)
    df.to_csv(out / "synthetic_student_daily.csv", index=False)
    pd.Series(asdict(cfg)).to_json(out / "simulator_config.json", indent=2)
    print(f"Generated {len(df):,} rows for {cfg.n_students} students x {cfg.n_days} days")
    print(df.head())

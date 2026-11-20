"""Run the isolated Twin integrity ML regeneration experiment."""
from __future__ import annotations

import argparse
from pathlib import Path

from ml.twin_integrity_experiment import run_twin_integrity_experiment


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate Phase 3 features and train candidate ML artifacts without touching production."
    )
    parser.add_argument(
        "--experiment-root",
        default="experiments/twin_integrity_fix",
        help="Directory for regenerated data, reports, and candidate artifacts.",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Skip creating a fresh copy-only archive of current production artifacts.",
    )
    parser.add_argument(
        "--existing-archive",
        default=None,
        help="Existing archive directory to record in the final report.",
    )
    args = parser.parse_args()

    report = run_twin_integrity_experiment(
        experiment_root=Path(args.experiment_root),
        create_archive=not args.no_archive,
        existing_archive_dir=Path(args.existing_archive) if args.existing_archive else None,
    )
    selected = report["candidate_metadata"]["model_selection"]["selected_model_name"]
    artifact = report["candidate_metadata"]["model_selection"]["candidate_artifact"]
    print("\nTwin integrity experiment complete")
    print(f"  Selected candidate model: {selected}")
    print(f"  Candidate artifact: {artifact}")
    print(f"  Final report: {Path(args.experiment_root) / 'final_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

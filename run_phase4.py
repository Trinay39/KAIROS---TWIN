#!/usr/bin/env python
"""
KAIROS-TWIN Phase 4: Run Complete Experiment.

Execute the full ML pipeline and generate results.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ml.experiment import Experiment


def main():
    """Run experiment."""
    print("\n" + "=" * 70)
    print("KAIROS-TWIN PHASE 4: ML PREDICTION PIPELINE")
    print("=" * 70)

    # Create experiment
    exp = Experiment(
        output_dir='experiments/results',
        random_state=42,
        verbose=True
    )

    # Run pipeline
    try:
        results = exp.run()
        print("\n[OK] Phase 4 experiment completed successfully!")
        return 0
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

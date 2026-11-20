"""
KAIROS-TWIN Phase 4: Utilities.

Helper functions and constants.
"""
import json
from pathlib import Path


def save_json(data: dict, path: str) -> None:
    """Save dict to JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_json(path: str) -> dict:
    """Load dict from JSON."""
    with open(path, 'r') as f:
        return json.load(f)

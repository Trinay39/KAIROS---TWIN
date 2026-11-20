"""Persistence helpers for Phase 7's isolated prototype JSON storage."""
from __future__ import annotations

from pathlib import Path
from threading import RLock


class Phase7Persistence:
    """
    Owns Phase 7's persistence paths and a single-process lock.

    This class does not expose client-configurable paths. That keeps persistence
    isolated under data/phase7 and avoids arbitrary filesystem access.
    """

    def __init__(self, base_dir: str = "data/phase7"):
        self.base_dir = Path(base_dir)
        self.lock = RLock()
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.registry_path = self._inside("intervention_registry.json")
        self.tracker_path = self._inside("outcome_tracker.json")
        self.audit_path = self._inside("request_audit.jsonl")

    def _inside(self, name: str) -> Path:
        path = self.base_dir / name
        base = self.base_dir.resolve()
        resolved = path.resolve()
        if base != resolved and base not in resolved.parents:
            raise ValueError("Phase 7 persistence path escaped data/phase7")
        return path

    def as_strings(self) -> tuple[str, str]:
        """Return registry and tracker paths for frozen Phase 6 components."""
        return str(self.registry_path), str(self.tracker_path)


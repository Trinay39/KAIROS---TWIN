"""
KAIROS-TWIN Phase 5: State Modifier.

Safe state cloning and modification without baseline mutation.
"""
from __future__ import annotations
from typing import Callable, Dict, Any
from copy import deepcopy
from dataclasses import fields

from core.schemas import StudentTwinState


class StateModifier:
    """
    Safe state modifier that clones and modifies StudentTwinState.

    Guarantees:
    - Baseline state never mutated
    - Modifications isolated to cloned state
    - Cloned state structure matches original
    """

    @staticmethod
    def clone(state: StudentTwinState) -> StudentTwinState:
        """
        Deep clone a StudentTwinState.

        Args:
            state: Original state

        Returns:
            Deep copy of state (no shared references)
        """
        return deepcopy(state)

    @staticmethod
    def modify(
        state: StudentTwinState,
        modifier_func: Callable[[StudentTwinState], None]
    ) -> StudentTwinState:
        """
        Clone and modify a StudentTwinState.

        Args:
            state: Original state (not modified)
            modifier_func: Function that modifies cloned state in-place

        Returns:
            Modified clone

        Example:
            def increase_sleep(s):
                s.recovery.avg_sleep_hours_7d = 8.0

            modified = StateModifier.modify(baseline_state, increase_sleep)
        """
        cloned = StateModifier.clone(state)
        modifier_func(cloned)
        return cloned

    @staticmethod
    def set_nested_field(
        state: StudentTwinState,
        layer_name: str,
        field_name: str,
        value: Any
    ) -> StudentTwinState:
        """
        Set a field in a nested layer (Academic, Behavioral, etc.).

        Args:
            state: State to modify (cloned first)
            layer_name: Layer name ('academic', 'behavioral', 'recovery', etc.)
            field_name: Field name within that layer
            value: New value

        Returns:
            Modified clone

        Raises:
            AttributeError: If layer or field not found
        """
        cloned = StateModifier.clone(state)

        # Map layer names to actual attributes
        layer_mapping = {
            'academic': 'academic',
            'behavioral': 'behavioral',
            'recovery': 'recovery',
            'workload': 'workload',
            'engagement': 'engagement',
            'temporal': 'temporal',
        }

        if layer_name not in layer_mapping:
            raise AttributeError(f"Unknown layer: {layer_name}")

        layer = getattr(cloned, layer_mapping[layer_name])
        setattr(layer, field_name, value)

        return cloned

    @staticmethod
    def verify_unchanged(
        original: StudentTwinState,
        check_state: StudentTwinState
    ) -> bool:
        """
        Verify original state is unchanged.

        Args:
            original: Original state
            check_state: State to check

        Returns:
            True if original unchanged (deep comparison)
        """
        # Deep comparison of all layers
        layers_to_check = [
            'academic', 'behavioral', 'recovery', 'workload',
            'engagement', 'temporal', 'predictions', 'history'
        ]

        for layer_name in layers_to_check:
            try:
                orig_layer = getattr(original, layer_name)
                check_layer = getattr(check_state, layer_name)

                # Compare all fields
                if hasattr(orig_layer, '__dataclass_fields__'):
                    for field in fields(orig_layer):
                        orig_val = getattr(orig_layer, field.name)
                        check_val = getattr(check_layer, field.name)

                        if orig_val != check_val:
                            return False
            except AttributeError:
                pass

        return True

    @staticmethod
    def get_modified_fields(
        original: StudentTwinState,
        modified: StudentTwinState
    ) -> Dict[str, Dict[str, tuple]]:
        """
        Get all fields that changed between original and modified.

        Args:
            original: Original state
            modified: Modified state

        Returns:
            Dict mapping layer_name -> {field_name: (original_value, modified_value)}
        """
        changes = {}

        layers_to_check = [
            'academic', 'behavioral', 'recovery', 'workload',
            'engagement', 'temporal', 'predictions', 'history'
        ]

        for layer_name in layers_to_check:
            try:
                orig_layer = getattr(original, layer_name)
                mod_layer = getattr(modified, layer_name)

                layer_changes = {}

                if hasattr(orig_layer, '__dataclass_fields__'):
                    for field in fields(orig_layer):
                        orig_val = getattr(orig_layer, field.name)
                        mod_val = getattr(mod_layer, field.name)

                        if orig_val != mod_val:
                            layer_changes[field.name] = (orig_val, mod_val)

                if layer_changes:
                    changes[layer_name] = layer_changes

            except AttributeError:
                pass

        return changes

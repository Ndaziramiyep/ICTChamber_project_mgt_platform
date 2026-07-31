"""Ordering math for placing a task among its siblings within a column.

Positions are floats so that inserting a task between two existing neighbors is an O(1)
midpoint computation, rather than renumbering every sibling on each drag-and-drop move.
"""

from __future__ import annotations

DEFAULT_POSITION_GAP: float = 1000.0
MINIMUM_POSITION_GAP_THRESHOLD: float = 0.001


def calculate_position_between_neighbors(
    position_before_value: float | None,
    position_after_value: float | None,
) -> float:
    """Return the position value a task should take between the given ordered neighbors.

    Either neighbor may be ``None`` to represent the top of the column
    (``position_before_value`` is ``None``), the bottom of the column
    (``position_after_value`` is ``None``), or an empty column (both are ``None``).
    """
    if position_before_value is None and position_after_value is None:
        return DEFAULT_POSITION_GAP

    if position_before_value is None:
        assert position_after_value is not None
        return position_after_value - DEFAULT_POSITION_GAP

    if position_after_value is None:
        return position_before_value + DEFAULT_POSITION_GAP

    return (position_before_value + position_after_value) / 2


def requires_position_rebalance(
    position_before_value: float | None,
    position_after_value: float | None,
) -> bool:
    """Return whether the gap between two neighbors is too small to safely insert between them.

    Repeated midpoint insertions at the same spot eventually exhaust floating-point precision;
    once the remaining gap falls under ``MINIMUM_POSITION_GAP_THRESHOLD`` the caller should run
    a rebalance pass (see ``generate_sequential_position_values``) instead of inserting further.
    """
    if position_before_value is None or position_after_value is None:
        return False

    return (position_after_value - position_before_value) < MINIMUM_POSITION_GAP_THRESHOLD


def generate_sequential_position_values(total_number_of_tasks: int) -> list[float]:
    """Return evenly spaced position values, one per task, for a full-column rebalance pass."""
    return [
        DEFAULT_POSITION_GAP * sequential_task_number
        for sequential_task_number in range(1, total_number_of_tasks + 1)
    ]

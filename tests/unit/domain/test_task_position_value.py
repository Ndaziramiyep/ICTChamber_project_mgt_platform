"""Unit tests for the task ordering math used to support drag-and-drop repositioning."""

from __future__ import annotations

from app.domain.value_objects.task_position_value import (
    DEFAULT_POSITION_GAP,
    calculate_position_between_neighbors,
    generate_sequential_position_values,
    requires_position_rebalance,
)


class TestCalculatePositionBetweenNeighbors:
    """Behavior of calculate_position_between_neighbors across all drag-and-drop drop targets."""

    def test_returns_default_gap_value_when_column_is_empty(self) -> None:
        computed_position_value = calculate_position_between_neighbors(
            position_before_value=None,
            position_after_value=None,
        )

        assert computed_position_value == DEFAULT_POSITION_GAP

    def test_returns_midpoint_when_both_neighbors_are_given(self) -> None:
        computed_position_value = calculate_position_between_neighbors(
            position_before_value=1000.0,
            position_after_value=2000.0,
        )

        assert computed_position_value == 1500.0

    def test_subtracts_gap_when_task_is_moved_to_the_top(self) -> None:
        computed_position_value = calculate_position_between_neighbors(
            position_before_value=None,
            position_after_value=1000.0,
        )

        assert computed_position_value == 1000.0 - DEFAULT_POSITION_GAP

    def test_adds_gap_when_task_is_moved_to_the_bottom(self) -> None:
        computed_position_value = calculate_position_between_neighbors(
            position_before_value=1000.0,
            position_after_value=None,
        )

        assert computed_position_value == 1000.0 + DEFAULT_POSITION_GAP


class TestRequiresPositionRebalance:
    """Behavior of requires_position_rebalance, the float-precision-exhaustion detector."""

    def test_returns_true_when_gap_between_neighbors_is_too_small(self) -> None:
        assert (
            requires_position_rebalance(
                position_before_value=1000.0,
                position_after_value=1000.0000001,
            )
            is True
        )

    def test_returns_false_when_gap_between_neighbors_is_sufficient(self) -> None:
        assert (
            requires_position_rebalance(
                position_before_value=1000.0,
                position_after_value=2000.0,
            )
            is False
        )

    def test_returns_false_when_only_one_neighbor_is_given(self) -> None:
        assert (
            requires_position_rebalance(
                position_before_value=1000.0,
                position_after_value=None,
            )
            is False
        )

    def test_returns_false_when_column_is_empty(self) -> None:
        assert (
            requires_position_rebalance(
                position_before_value=None,
                position_after_value=None,
            )
            is False
        )


class TestGenerateSequentialPositionValues:
    """Behavior of generate_sequential_position_values, used by the rebalance/compaction pass."""

    def test_returns_evenly_spaced_positions_for_requested_task_count(self) -> None:
        sequential_position_values = generate_sequential_position_values(
            total_number_of_tasks=3,
        )

        assert sequential_position_values == [
            DEFAULT_POSITION_GAP,
            DEFAULT_POSITION_GAP * 2,
            DEFAULT_POSITION_GAP * 3,
        ]

    def test_returns_empty_list_when_no_tasks_requested(self) -> None:
        assert generate_sequential_position_values(total_number_of_tasks=0) == []

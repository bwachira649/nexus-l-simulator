"""Tests for computing-cell resource accounting."""

import pytest

from nexus_l.cell import CellStatus, ComputeCell


def make_cell() -> ComputeCell:
    return ComputeCell("cell-01", cpu_capacity=8.0, memory_mb=4096)


def test_new_cell_starts_online_with_full_capacity() -> None:
    cell = make_cell()

    assert cell.status == CellStatus.ONLINE
    assert cell.available_cpu == 8.0
    assert cell.available_memory_mb == 4096
    assert cell.is_available


def test_allocation_and_release_update_resources() -> None:
    cell = make_cell()

    cell.allocate(2.5, 1024)

    assert cell.available_cpu == 5.5
    assert cell.available_memory_mb == 3072

    cell.release(2.5, 1024)

    assert cell.available_cpu == 8.0
    assert cell.available_memory_mb == 4096


def test_allocation_failure_does_not_partially_change_resources() -> None:
    cell = make_cell()

    with pytest.raises(RuntimeError):
        cell.allocate(9.0, 1024)

    assert cell.cpu_used == 0
    assert cell.memory_used_mb == 0


def test_offline_cell_cannot_accept_workloads() -> None:
    cell = make_cell()
    cell.status = CellStatus.OFFLINE

    assert not cell.is_available
    assert not cell.can_run(1.0, 128)

    with pytest.raises(RuntimeError):
        cell.allocate(1.0, 128)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"cell_id": ""}, "cell_id"),
        ({"cpu_capacity": 0}, "cpu_capacity"),
        ({"memory_mb": 0}, "memory_mb"),
        ({"cpu_used": 9}, "cpu_used"),
        ({"memory_used_mb": 5000}, "memory_used_mb"),
    ],
)
def test_invalid_cell_configuration_is_rejected(
    kwargs: dict[str, object], message: str
) -> None:
    values: dict[str, object] = {
        "cell_id": "cell-test",
        "cpu_capacity": 8.0,
        "memory_mb": 4096,
    }
    values.update(kwargs)

    with pytest.raises(ValueError, match=message):
        ComputeCell(**values)  # type: ignore[arg-type]


def test_invalid_workload_requirements_are_rejected() -> None:
    cell = make_cell()

    with pytest.raises(ValueError):
        cell.can_run(0, 128)

    with pytest.raises(ValueError):
        cell.can_run(1, 0)


def test_cell_cannot_be_its_own_neighbour() -> None:
    with pytest.raises(ValueError, match="own neighbour"):
        ComputeCell("cell-01", 8.0, 4096, neighbours={"cell-01"})

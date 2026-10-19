"""Tests for resource-aware workload scheduling."""

import pytest

from nexus_l.cell import CellStatus, ComputeCell
from nexus_l.network import ComputeNetwork
from nexus_l.scheduler import Workload, WorkloadScheduler, WorkloadStatus


def make_scheduler() -> WorkloadScheduler:
    network = ComputeNetwork()
    network.add_cell(ComputeCell("cell-A", 8.0, 4096))
    network.add_cell(ComputeCell("cell-B", 4.0, 2048))
    return WorkloadScheduler(network)


def test_workload_is_assigned_to_a_fitting_cell() -> None:
    scheduler = make_scheduler()
    workload = Workload("job-1", 2.0, 512)

    assert scheduler.submit(workload) == WorkloadStatus.RUNNING
    assert workload.assigned_cell is not None
    assert scheduler.network.cells[workload.assigned_cell].cpu_used == 2.0


def test_scheduler_selects_cell_with_lowest_projected_utilization() -> None:
    scheduler = make_scheduler()
    workload = Workload("job-1", 1.0, 256)

    scheduler.submit(workload)

    assert workload.assigned_cell == "cell-A"


def test_completion_releases_reserved_resources() -> None:
    scheduler = make_scheduler()
    workload = Workload("job-1", 2.0, 512)
    scheduler.submit(workload)
    cell_id = workload.assigned_cell
    assert cell_id is not None

    scheduler.complete("job-1")

    assert workload.status == WorkloadStatus.COMPLETED
    assert scheduler.network.cells[cell_id].cpu_used == 0
    assert scheduler.network.cells[cell_id].memory_used_mb == 0


def test_workload_is_rejected_when_no_cell_has_capacity() -> None:
    scheduler = make_scheduler()
    workload = Workload("large-job", 100.0, 1024)

    assert scheduler.submit(workload) == WorkloadStatus.REJECTED
    assert all(cell.cpu_used == 0 for cell in scheduler.network.cells.values())


def test_offline_cells_are_not_selected() -> None:
    scheduler = make_scheduler()
    scheduler.network.set_status("cell-A", CellStatus.OFFLINE)
    workload = Workload("job-1", 1.0, 256)

    scheduler.submit(workload)

    assert workload.assigned_cell == "cell-B"


def test_duplicate_workload_is_rejected() -> None:
    scheduler = make_scheduler()
    scheduler.submit(Workload("job-1", 1.0, 256))

    with pytest.raises(ValueError, match="already exists"):
        scheduler.submit(Workload("job-1", 1.0, 256))


def test_unknown_workload_cannot_be_completed() -> None:
    scheduler = make_scheduler()

    with pytest.raises(KeyError, match="Unknown workload"):
        scheduler.complete("missing")


def test_pending_or_rejected_workload_cannot_be_completed() -> None:
    scheduler = make_scheduler()
    scheduler.submit(Workload("job-1", 100.0, 256))

    with pytest.raises(ValueError, match="Only running"):
        scheduler.complete("job-1")


@pytest.mark.parametrize(
    ("workload_id", "cpu", "memory"),
    [
        ("", 1.0, 256),
        ("job", 0.0, 256),
        ("job", float("inf"), 256),
        ("job", 1.0, 0),
    ],
)
def test_invalid_workload_is_rejected(
    workload_id: str, cpu: float, memory: int
) -> None:
    with pytest.raises(ValueError):
        Workload(workload_id, cpu, memory)


def test_scheduler_summary_tracks_lifecycle() -> None:
    scheduler = make_scheduler()
    scheduler.submit(Workload("job-1", 1.0, 256))
    scheduler.submit(Workload("job-2", 100.0, 256))
    scheduler.complete("job-1")

    assert scheduler.summary() == {
        "pending": 0,
        "running": 0,
        "completed": 1,
        "rejected": 1,
        "failed": 0,
    }


def test_preassigned_workload_cannot_be_submitted() -> None:
    scheduler = make_scheduler()
    workload = Workload("job-1", 1.0, 256, assigned_cell="cell-A")

    with pytest.raises(ValueError, match="already have an assigned"):
        scheduler.submit(workload)

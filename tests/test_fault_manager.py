"""Tests for cell failure detection and workload impact tracking."""

from nexus_l.cell import CellStatus, ComputeCell
from nexus_l.fault_manager import FaultManager
from nexus_l.network import ComputeNetwork
from nexus_l.scheduler import Workload, WorkloadScheduler, WorkloadStatus


def build_system() -> tuple[ComputeNetwork, WorkloadScheduler, FaultManager]:
    network = ComputeNetwork()
    network.add_cell(ComputeCell("A", 8.0, 4096))
    network.add_cell(ComputeCell("B", 4.0, 2048))
    network.connect("A", "B")

    scheduler = WorkloadScheduler(network)
    faults = FaultManager(network, scheduler)
    return network, scheduler, faults


def test_detects_offline_cell() -> None:
    network, _, faults = build_system()
    network.set_status("B", CellStatus.OFFLINE)

    events = faults.detect_failures()

    assert len(events) == 1
    assert events[0].cell_id == "B"
    assert events[0].affected_workloads == ()


def test_marks_workload_failed_when_assigned_cell_goes_offline() -> None:
    network, scheduler, faults = build_system()
    workload = Workload("job-1", 1.0, 256)
    scheduler.submit(workload)

    assert workload.assigned_cell == "A"

    network.set_status("A", CellStatus.OFFLINE)
    events = faults.detect_failures()

    assert workload.status == WorkloadStatus.FAILED
    assert events[0].affected_workloads == ("job-1",)


def test_detection_does_not_duplicate_existing_failure_events() -> None:
    network, _, faults = build_system()
    network.set_status("B", CellStatus.OFFLINE)

    assert len(faults.detect_failures()) == 1
    assert faults.detect_failures() == []
    assert len(faults.events) == 1


def test_running_workload_on_another_cell_is_not_failed() -> None:
    network, scheduler, faults = build_system()
    workload = Workload("job-1", 1.0, 256)
    scheduler.submit(workload)

    network.set_status("B", CellStatus.OFFLINE)
    faults.detect_failures()

    assert workload.status == WorkloadStatus.RUNNING


def test_event_log_is_json_serializable() -> None:
    network, _, faults = build_system()
    network.set_status("B", CellStatus.OFFLINE)
    faults.detect_failures()

    log = faults.event_log()

    assert len(log) == 1
    assert log[0]["cell_id"] == "B"
    assert isinstance(log[0]["timestamp"], str)
    assert log[0]["affected_workloads"] == []

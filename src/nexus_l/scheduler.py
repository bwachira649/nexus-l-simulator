"""Workload definitions and resource-aware scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from nexus_l.cell import ComputeCell
from nexus_l.network import ComputeNetwork


class WorkloadStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass(slots=True)
class Workload:
    """A workload with explicit resource requirements."""

    workload_id: str
    cpu_required: float
    memory_required_mb: int
    status: WorkloadStatus = WorkloadStatus.PENDING
    assigned_cell: str | None = None

    def __post_init__(self) -> None:
        if not self.workload_id.strip():
            raise ValueError("workload_id must not be empty")
        if not isfinite(self.cpu_required) or self.cpu_required <= 0:
            raise ValueError("cpu_required must be finite and positive")
        if self.memory_required_mb <= 0:
            raise ValueError("memory_required_mb must be positive")


class WorkloadScheduler:
    """Schedule workloads using available resources and deterministic scoring."""

    def __init__(self, network: ComputeNetwork) -> None:
        self.network = network
        self.workloads: dict[str, Workload] = {}

    def submit(self, workload: Workload) -> str:
        """Register and attempt to schedule a workload."""
        if workload.workload_id in self.workloads:
            raise ValueError(f"Workload {workload.workload_id!r} already exists")
        if workload.status != WorkloadStatus.PENDING:
            raise ValueError("Only pending workloads can be submitted")
        if workload.assigned_cell is not None:
            raise ValueError("A new workload cannot already have an assigned cell")

        self.workloads[workload.workload_id] = workload
        cell = self._select_cell(workload)

        if cell is None:
            workload.status = WorkloadStatus.REJECTED
            return workload.status

        cell.allocate(workload.cpu_required, workload.memory_required_mb)
        workload.assigned_cell = cell.cell_id
        workload.status = WorkloadStatus.RUNNING
        return workload.status

    def _select_cell(self, workload: Workload) -> ComputeCell | None:
        """Choose a fitting online cell with the lowest projected utilization."""
        candidates = [
            cell
            for cell in self.network.cells.values()
            if cell.can_run(workload.cpu_required, workload.memory_required_mb)
        ]

        if not candidates:
            return None

        def score(cell: ComputeCell) -> tuple[float, float, str]:
            cpu_ratio = (
                cell.cpu_used + workload.cpu_required
            ) / cell.cpu_capacity
            memory_ratio = (
                cell.memory_used_mb + workload.memory_required_mb
            ) / cell.memory_mb
            return max(cpu_ratio, memory_ratio), cpu_ratio + memory_ratio, cell.cell_id

        return min(candidates, key=score)

    def complete(self, workload_id: str) -> None:
        """Complete a running workload and release its resource reservations."""
        workload = self._get_workload(workload_id)

        if workload.status != WorkloadStatus.RUNNING:
            raise ValueError("Only running workloads can be completed")
        if workload.assigned_cell is None:
            raise RuntimeError("Running workload has no assigned cell")

        cell = self.network.cells[workload.assigned_cell]
        cell.release(workload.cpu_required, workload.memory_required_mb)
        workload.status = WorkloadStatus.COMPLETED

    def _get_workload(self, workload_id: str) -> Workload:
        try:
            return self.workloads[workload_id]
        except KeyError:
            raise KeyError(f"Unknown workload: {workload_id!r}") from None

    def summary(self) -> dict[str, int]:
        """Count workloads by lifecycle status."""
        return {
            status.value: sum(
                workload.status == status for workload in self.workloads.values()
            )
            for status in WorkloadStatus
        }

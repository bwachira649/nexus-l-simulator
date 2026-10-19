"""Core models for the NEXUS-L distributed computing simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite


class CellStatus(StrEnum):
    """Operational state of a computing cell."""

    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


@dataclass(slots=True)
class ComputeCell:
    """A simulated computing node with bounded resources and health."""

    cell_id: str
    cpu_capacity: float
    memory_mb: int
    status: CellStatus = CellStatus.ONLINE
    cpu_used: float = 0.0
    memory_used_mb: int = 0
    neighbours: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.cell_id.strip():
            raise ValueError("cell_id must not be empty")
        if not isfinite(self.cpu_capacity) or self.cpu_capacity <= 0:
            raise ValueError("cpu_capacity must be finite and positive")
        if self.memory_mb <= 0:
            raise ValueError("memory_mb must be positive")
        if not 0 <= self.cpu_used <= self.cpu_capacity:
            raise ValueError("cpu_used must be within CPU capacity")
        if not 0 <= self.memory_used_mb <= self.memory_mb:
            raise ValueError("memory_used_mb must be within memory capacity")
        if self.cell_id in self.neighbours:
            raise ValueError("a cell cannot be its own neighbour")

    @property
    def available_cpu(self) -> float:
        """Return the remaining CPU capacity."""
        return self.cpu_capacity - self.cpu_used

    @property
    def available_memory_mb(self) -> int:
        """Return the remaining memory in megabytes."""
        return self.memory_mb - self.memory_used_mb

    @property
    def is_available(self) -> bool:
        """Whether the cell is online and has some capacity remaining."""
        return (
            self.status == CellStatus.ONLINE
            and self.available_cpu > 0
            and self.available_memory_mb > 0
        )

    def can_run(self, cpu_required: float, memory_required_mb: int) -> bool:
        """Check whether a workload fits without changing the cell."""
        if not isfinite(cpu_required) or cpu_required <= 0:
            raise ValueError("cpu_required must be finite and positive")
        if memory_required_mb <= 0:
            raise ValueError("memory_required_mb must be positive")
        return (
            self.status == CellStatus.ONLINE
            and self.available_cpu >= cpu_required
            and self.available_memory_mb >= memory_required_mb
        )

    def allocate(self, cpu_required: float, memory_required_mb: int) -> None:
        """Reserve resources for a workload or fail without partial allocation."""
        if not self.can_run(cpu_required, memory_required_mb):
            raise RuntimeError(
                f"Cell {self.cell_id!r} cannot satisfy the requested resources"
            )
        self.cpu_used += cpu_required
        self.memory_used_mb += memory_required_mb

    def release(self, cpu_amount: float, memory_amount_mb: int) -> None:
        """Release previously reserved resources."""
        if not isfinite(cpu_amount) or cpu_amount <= 0:
            raise ValueError("cpu_amount must be finite and positive")
        if memory_amount_mb <= 0:
            raise ValueError("memory_amount_mb must be positive")
        if cpu_amount > self.cpu_used or memory_amount_mb > self.memory_used_mb:
            raise ValueError("cannot release more resources than currently allocated")
        self.cpu_used -= cpu_amount
        self.memory_used_mb -= memory_amount_mb

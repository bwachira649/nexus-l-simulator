"""Failure detection and workload impact tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from nexus_l.cell import CellStatus
from nexus_l.network import ComputeNetwork
from nexus_l.scheduler import WorkloadScheduler, WorkloadStatus


@dataclass(frozen=True, slots=True)
class FailureEvent:
    """An observed computing-cell failure."""

    cell_id: str
    timestamp: str
    affected_workloads: tuple[str, ...]


@dataclass
class FaultManager:
    """Record offline cells and account for affected running workloads."""

    network: ComputeNetwork
    scheduler: WorkloadScheduler
    events: list[FailureEvent] = field(default_factory=list)

    def detect_failures(self) -> list[FailureEvent]:
        """Discover offline cells and record previously unreported failures."""
        known_cells = {event.cell_id for event in self.events}
        new_events: list[FailureEvent] = []

        for cell_id, cell in self.network.cells.items():
            if cell.status != CellStatus.OFFLINE or cell_id in known_cells:
                continue

            affected: list[str] = []

            for workload in self.scheduler.workloads.values():
                if (
                    workload.assigned_cell == cell_id
                    and workload.status == WorkloadStatus.RUNNING
                ):
                    workload.status = WorkloadStatus.FAILED
                    affected.append(workload.workload_id)

            event = FailureEvent(
                cell_id=cell_id,
                timestamp=datetime.now(UTC).isoformat(),
                affected_workloads=tuple(sorted(affected)),
            )
            self.events.append(event)
            new_events.append(event)

        return new_events

    def event_log(self) -> list[dict[str, object]]:
        """Return failure events in a JSON-serializable format."""
        return [
            {
                "cell_id": event.cell_id,
                "timestamp": event.timestamp,
                "affected_workloads": list(event.affected_workloads),
            }
            for event in self.events
        ]

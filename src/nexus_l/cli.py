"""Run a reproducible NEXUS-L network and fault-management demonstration."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

import networkx as nx

from nexus_l.cell import CellStatus, ComputeCell
from nexus_l.fault_manager import FaultManager
from nexus_l.network import ComputeNetwork
from nexus_l.scheduler import Workload, WorkloadScheduler


def build_demo_network() -> ComputeNetwork:
    """Build a four-cell network with two routes between its endpoints."""
    network = ComputeNetwork()

    for cell_id, cpu, memory in (
        ("cell-A", 8.0, 8192),
        ("cell-B", 4.0, 4096),
        ("cell-C", 6.0, 6144),
        ("cell-D", 8.0, 8192),
    ):
        network.add_cell(ComputeCell(cell_id, cpu, memory))

    network.connect("cell-A", "cell-B", 2.0)
    network.connect("cell-B", "cell-D", 2.0)
    network.connect("cell-A", "cell-C", 1.0)
    network.connect("cell-C", "cell-D", 8.0)

    return network


def run_demo() -> dict[str, object]:
    """Simulate scheduling, a cell failure, detection, and route recovery."""
    network = build_demo_network()
    scheduler = WorkloadScheduler(network)
    fault_manager = FaultManager(network, scheduler)

    initial_route = network.route("cell-A", "cell-D")
    initial_latency = network.route_latency_ms(initial_route)

    # Constrain placement so the workload is deterministically assigned to B.
    network.set_status("cell-A", CellStatus.OFFLINE)
    network.set_status("cell-C", CellStatus.OFFLINE)
    network.set_status("cell-D", CellStatus.OFFLINE)

    workload = Workload(
        workload_id="demo-job-001",
        cpu_required=2.0,
        memory_required_mb=1024,
    )
    scheduler.submit(workload)

    network.set_status("cell-A", CellStatus.ONLINE)
    network.set_status("cell-C", CellStatus.ONLINE)
    network.set_status("cell-D", CellStatus.ONLINE)

    if workload.assigned_cell != "cell-B":
        raise RuntimeError(
            "Demo setup failed: expected demo-job-001 on cell-B, "
            f"got {workload.assigned_cell!r}."
        )

    network.set_status("cell-B", CellStatus.OFFLINE)
    detected_failures = fault_manager.detect_failures()

    try:
        recovered_route = network.route("cell-A", "cell-D")
        recovered_latency = network.route_latency_ms(recovered_route)
    except nx.NetworkXNoPath:
        recovered_route = None
        recovered_latency = None

    return {
        "simulation": "NEXUS-L",
        "version": "0.1.0",
        "initial_route": initial_route,
        "initial_latency_ms": initial_latency,
        "failed_cell": "cell-B",
        "failure_detection": {
            "new_events": len(detected_failures),
            "events": fault_manager.event_log(),
        },
        "recovered_route": recovered_route,
        "recovered_latency_ms": recovered_latency,
        "workloads": [
            {
                "id": item.workload_id,
                "status": item.status.value,
                "assigned_cell": item.assigned_cell,
            }
            for item in scheduler.workloads.values()
        ],
        "network": network.summary(),
        "scheduler": scheduler.summary(),
    }


def main(argv: Sequence[str] | None = None) -> None:
    """Print results as JSON or save them to a JSON report."""
    parser = argparse.ArgumentParser(
        description="Run the NEXUS-L distributed-computing simulation."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Save the simulation report to this JSON file.",
    )
    args = parser.parse_args(argv)

    report = json.dumps(run_demo(), indent=2) + "\n"

    if args.output is None:
        print(report, end="")
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Simulation report saved to: {args.output}")


if __name__ == "__main__":
    main()

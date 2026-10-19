"""Tests for the NEXUS-L command-line simulation."""

import json

from nexus_l.cli import build_demo_network, main, run_demo


def test_demo_network_has_four_cells_and_four_links() -> None:
    network = build_demo_network()

    assert network.summary() == {
        "cells": 4,
        "links": 4,
        "online": 4,
        "offline": 0,
        "degraded": 0,
    }


def test_demo_reroutes_after_cell_failure() -> None:
    result = run_demo()

    assert result["initial_route"] == ["cell-A", "cell-B", "cell-D"]
    assert result["recovered_route"] == ["cell-A", "cell-C", "cell-D"]
    assert result["failed_cell"] == "cell-B"
    assert result["initial_latency_ms"] == 4.0
    assert result["recovered_latency_ms"] == 9.0


def test_demo_tracks_failed_workload() -> None:
    result = run_demo()
    workloads = result["workloads"]

    assert len(workloads) == 1
    assert workloads[0]["id"] == "demo-job-001"
    assert workloads[0]["status"] == "failed"
    assert workloads[0]["assigned_cell"] == "cell-B"


def test_demo_records_failure_impact() -> None:
    result = run_demo()
    detection = result["failure_detection"]

    assert detection["new_events"] == 1
    assert len(detection["events"]) == 1
    assert detection["events"][0]["cell_id"] == "cell-B"
    assert detection["events"][0]["affected_workloads"] == ["demo-job-001"]
    assert detection["events"][0]["timestamp"]


def test_demo_reports_offline_cell() -> None:
    result = run_demo()

    assert result["network"] == {
        "cells": 4,
        "links": 4,
        "online": 3,
        "offline": 1,
        "degraded": 0,
    }


def test_demo_scheduler_counts_failed_workload() -> None:
    result = run_demo()

    assert result["scheduler"] == {
        "pending": 0,
        "running": 0,
        "completed": 0,
        "rejected": 0,
        "failed": 1,
    }


def test_demo_results_are_reproducible_except_for_timestamp() -> None:
    first = run_demo()
    second = run_demo()

    first["failure_detection"]["events"][0].pop("timestamp")
    second["failure_detection"]["events"][0].pop("timestamp")

    assert first == second


def test_cli_exports_json_report(tmp_path) -> None:
    output = tmp_path / "reports" / "simulation.json"

    main(["--output", str(output)])

    report = json.loads(output.read_text(encoding="utf-8"))

    assert report["simulation"] == "NEXUS-L"
    assert report["failed_cell"] == "cell-B"
    assert report["recovered_route"] == ["cell-A", "cell-C", "cell-D"]
    assert report["scheduler"]["failed"] == 1

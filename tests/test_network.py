"""Tests for topology, link management, and resilient routing."""

import networkx as nx
import pytest

from nexus_l.cell import CellStatus, ComputeCell
from nexus_l.network import ComputeNetwork


def make_network() -> ComputeNetwork:
    network = ComputeNetwork()
    for cell_id in ("A", "B", "C", "D"):
        network.add_cell(ComputeCell(cell_id, 8.0, 4096))

    network.connect("A", "B", 2.0)
    network.connect("B", "D", 2.0)
    network.connect("A", "C", 1.0)
    network.connect("C", "D", 8.0)
    return network


def test_network_tracks_cells_and_links() -> None:
    network = make_network()

    assert network.summary() == {
        "cells": 4,
        "links": 4,
        "online": 4,
        "offline": 0,
        "degraded": 0,
    }


def test_route_chooses_lowest_latency_path() -> None:
    network = make_network()

    assert network.route("A", "D") == ["A", "B", "D"]
    assert network.route_latency_ms(["A", "B", "D"]) == 4.0


def test_route_avoids_offline_cell() -> None:
    network = make_network()
    network.set_status("B", CellStatus.OFFLINE)

    assert network.route("A", "D") == ["A", "C", "D"]


def test_route_fails_if_no_online_path_exists() -> None:
    network = make_network()
    network.set_status("B", CellStatus.OFFLINE)
    network.set_status("C", CellStatus.OFFLINE)

    with pytest.raises(nx.NetworkXNoPath):
        network.route("A", "D")


def test_offline_source_is_rejected() -> None:
    network = make_network()
    network.set_status("A", CellStatus.OFFLINE)

    with pytest.raises(nx.NetworkXNoPath):
        network.route("A", "D")


def test_duplicate_cell_is_rejected() -> None:
    network = make_network()

    with pytest.raises(ValueError, match="already exists"):
        network.add_cell(ComputeCell("A", 8.0, 4096))


@pytest.mark.parametrize("latency", [0, -1, float("inf"), float("nan")])
def test_invalid_latency_is_rejected(latency: float) -> None:
    network = make_network()

    with pytest.raises(ValueError, match="latency_ms"):
        network.connect("A", "D", latency)


def test_self_link_is_rejected() -> None:
    network = make_network()

    with pytest.raises(ValueError, match="itself"):
        network.connect("A", "A")


def test_unknown_cell_cannot_be_connected() -> None:
    network = make_network()

    with pytest.raises(KeyError):
        network.connect("A", "Z")


def test_disconnect_removes_link_and_neighbour_references() -> None:
    network = make_network()
    network.disconnect("A", "B")

    assert "B" not in network.cells["A"].neighbours
    assert "A" not in network.cells["B"].neighbours
    assert network.summary()["links"] == 3
    assert network.route("A", "D") == ["A", "C", "D"]


def test_unknown_status_target_is_rejected() -> None:
    network = make_network()

    with pytest.raises(KeyError, match="Unknown cell"):
        network.set_status("Z", CellStatus.OFFLINE)


def test_same_cell_route() -> None:
    network = make_network()

    assert network.route("A", "A") == ["A"]


def test_empty_or_invalid_latency_path_is_rejected() -> None:
    network = make_network()

    with pytest.raises(ValueError, match="empty"):
        network.route_latency_ms([])

    with pytest.raises(ValueError, match="missing link"):
        network.route_latency_ms(["A", "D"])

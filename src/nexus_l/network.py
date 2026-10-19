"""Network topology and routing for NEXUS-L."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

import networkx as nx

from nexus_l.cell import CellStatus, ComputeCell


@dataclass
class ComputeNetwork:
    """A network of computing cells connected by weighted links."""

    cells: dict[str, ComputeCell] = field(default_factory=dict)
    _graph: nx.Graph = field(default_factory=nx.Graph, repr=False)

    def add_cell(self, cell: ComputeCell) -> None:
        """Register a unique computing cell."""
        if cell.cell_id in self.cells:
            raise ValueError(f"Cell {cell.cell_id!r} already exists")

        self.cells[cell.cell_id] = cell
        self._graph.add_node(cell.cell_id)

    def connect(self, first: str, second: str, latency_ms: float = 1.0) -> None:
        """Connect two registered cells with a positive latency."""
        if first == second:
            raise ValueError("A cell cannot connect to itself")
        if first not in self.cells or second not in self.cells:
            raise KeyError("Both cells must be registered before connecting")
        if not isfinite(latency_ms) or latency_ms <= 0:
            raise ValueError("latency_ms must be finite and positive")

        self._graph.add_edge(first, second, latency_ms=latency_ms)
        self.cells[first].neighbours.add(second)
        self.cells[second].neighbours.add(first)

    def disconnect(self, first: str, second: str) -> None:
        """Remove a link between two cells."""
        if not self._graph.has_edge(first, second):
            raise KeyError(f"No link exists between {first!r} and {second!r}")

        self._graph.remove_edge(first, second)
        self.cells[first].neighbours.remove(second)
        self.cells[second].neighbours.remove(first)

    def set_status(self, cell_id: str, status: CellStatus) -> None:
        """Update a registered cell's operational state."""
        if cell_id not in self.cells:
            raise KeyError(f"Unknown cell: {cell_id!r}")
        self.cells[cell_id].status = status

    def route(self, source: str, destination: str) -> list[str]:
        """Find the lowest-latency route through online cells."""
        for cell_id in (source, destination):
            if cell_id not in self.cells:
                raise KeyError(f"Unknown cell: {cell_id!r}")

        if source == destination:
            if self.cells[source].status != CellStatus.ONLINE:
                raise nx.NetworkXNoPath("The requested cell is not online")
            return [source]

        if self.cells[source].status != CellStatus.ONLINE:
            raise nx.NetworkXNoPath(f"Source {source!r} is not online")
        if self.cells[destination].status != CellStatus.ONLINE:
            raise nx.NetworkXNoPath(f"Destination {destination!r} is not online")

        active_nodes = [
            cell_id
            for cell_id, cell in self.cells.items()
            if cell.status == CellStatus.ONLINE
        ]
        active_graph = self._graph.subgraph(active_nodes)

        return nx.shortest_path(
            active_graph,
            source=source,
            target=destination,
            weight="latency_ms",
        )

    def route_latency_ms(self, path: list[str]) -> float:
        """Calculate total link latency for a valid path."""
        if not path:
            raise ValueError("Path must not be empty")

        total = 0.0
        for first, second in zip(path, path[1:], strict=False):
            if not self._graph.has_edge(first, second):
                raise ValueError(f"Path contains a missing link: {first!r}-{second!r}")
            total += self._graph[first][second]["latency_ms"]

        return total

    def summary(self) -> dict[str, int]:
        """Return basic network and cell health counts."""
        return {
            "cells": len(self.cells),
            "links": self._graph.number_of_edges(),
            "online": sum(
                cell.status == CellStatus.ONLINE for cell in self.cells.values()
            ),
            "offline": sum(
                cell.status == CellStatus.OFFLINE for cell in self.cells.values()
            ),
            "degraded": sum(
                cell.status == CellStatus.DEGRADED for cell in self.cells.values()
            ),
        }

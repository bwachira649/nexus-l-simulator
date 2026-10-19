# NEXUS-L Simulator

NEXUS-L is an experimental distributed-computing simulator. Its long-term goal
is to explore resource-aware scheduling, network communication, fault detection,
and recovery across interconnected computing cells.

The project is a software simulation, not a new physical computer or a
production distributed-computing platform.

## Current status

Version 0.1.0: foundational computing-cell model.

- CPU and memory capacity accounting.
- Online, offline, and degraded cell states.
- Workload resource validation and allocation.
- Automated tests for resource safety.

## Requirements

- Python 3.12 or newer
- Git

## Setup on Windows

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
```

## Planned milestones

1. Computing-cell resource model.
2. Network topology and message routing.
3. Workload scheduling across eligible cells.
4. Failure detection and alternative routing.
5. Metrics, visualization, reproducible demonstrations, and documentation.

Milestones are plans, not claims of implemented functionality.

# NEXUS-L Simulator

NEXUS-L is an experimental Python simulator for exploring distributed computing, workload scheduling, network routing, and fault handling across interconnected compute cells.

It demonstrates how a simulated network can reroute traffic when a compute cell fails and how running workloads affected by that failure are recorded.

> **Project scope:** NEXUS-L is a software simulation, not a physical computer, production orchestration platform, or cloud service.

## Features

- **Compute cells:** Model CPU and memory capacity, resource allocation, and online, offline, and degraded states.
- **Network topology:** Connect cells with latency-aware links and find routes through available cells.
- **Workload scheduling:** Schedule workloads against available compute resources and track their lifecycle.
- **Fault detection:** Detect offline cells and record affected running workloads.
- **Resilience demonstration:** Compare the original route with an alternative route after a cell failure.
- **JSON evidence:** Export a simulation report containing routes, latency, workload status, failure events, and network health.
- **Automated tests and linting:** Validate core behavior with pytest and Ruff.

## Requirements

- Python 3.12 or newer
- pip

The project uses NetworkX for network graph operations.

## Setup

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### Linux or macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## Run the Simulation

From the project root:

```bash
python -m nexus_l.cli
```

If the package is not available in your active Python environment, install it using the setup instructions above.

## Export a JSON Report

### Windows PowerShell

```powershell
.\.venv\Scripts\python.exe -m nexus_l.cli --output .\evidence\simulation-report.json
Get-Content .\evidence\simulation-report.json
```

### Linux or macOS

```bash
.venv/bin/python -m nexus_l.cli --output evidence/simulation-report.json
cat evidence/simulation-report.json
```

The demonstration starts with a route through `cell-B`. When that cell fails, the simulator records the affected workload and calculates an alternative route through `cell-C`.

## Tests and Code Quality

Run the test suite:

```bash
python -m pytest -q
```

Run Ruff:

```bash
ruff check .
```

Use the virtual environment's Python and Ruff executables if the environment is not activated.

## Project Structure

```text
nexus-l-simulator/
├── docs/                  # Project documentation
├── evidence/              # Generated simulation evidence
├── scripts/               # Supporting scripts
├── src/nexus_l/
│   ├── cell.py             # Compute-cell model and resources
│   ├── network.py          # Topology and route calculation
│   ├── scheduler.py        # Workload scheduling and lifecycle
│   ├── fault_manager.py    # Failure detection and event records
│   └── cli.py              # Simulation and JSON export
├── tests/                  # Automated tests
├── pyproject.toml          # Package and tool configuration
└── README.md
```

## Current Status

Version `0.1.0`. The current implementation covers compute-cell modeling, network routing, workload scheduling, failure detection, and JSON report export.

The project remains an evolving simulation. Its behavior and limitations should be evaluated through its source code, automated tests, and generated evidence.

## License

License terms have not yet been established.
ented functionality.

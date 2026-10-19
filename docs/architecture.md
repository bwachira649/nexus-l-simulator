# Architecture Notes

## Initial design: computing cells

Each cell has a unique identifier, CPU capacity, memory capacity, resource
usage, operational state, and a set of neighbouring cell identifiers.

The initial resource model validates capacity limits before changing resource
usage. Allocation is all-or-nothing: an unsuccessful request must not reserve
only part of its requested resources.

## Planned architecture

- **Cell model:** resource accounting and operational state.
- **Network layer:** topology, links, message delivery, and routing.
- **Scheduler:** select eligible cells for workloads.
- **Fault manager:** detect unavailable cells and evaluate recovery options.
- **Observability:** event logs, network metrics, and visual demonstrations.

The network, scheduler, and fault manager will be implemented and tested in
subsequent milestones.

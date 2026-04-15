# Project Architecture

## Overview
The project separates simulation domain logic from execution interfaces.

## Layers
- `src/phoa/spatial_grid.py`: spatial modeling and obstacle dynamics.
- `src/phoa/drones.py`: domain entities (`Drone`, `Scout`, `Finisher`).
- `src/phoa/coordinator.py`: PHOA tactical-operational orchestration.
- `src/phoa/simulation.py`: simulation loop and aggregated metrics.
- `src/phoa/cli.py`: command-line entrypoint.
- `src/phoa/streamlit_app.py`: visual monitoring frontend.

## Architectural Decisions
- Object-oriented model for agent roles.
- Clear separation between UI (CLI/Streamlit) and algorithm core.
- `src layout` to improve packaging, testing, and distribution.

## Recommended Evolution
- Introduce a `services/` layer for batch experiment scenarios.
- Add telemetry persistence interfaces (CSV/Parquet/DB).
- Create a planner module for movement strategy replacement.

<div align="center">
  <h1>PHOA</h1>
  <p><i>Pride-Hunt Optimization Algorithm for drone coordination in SAR and urban logistics scenarios</i></p>

  <p>
    <a href="https://github.com/NullCipherr/phoa/actions/workflows/ci.yml"><img src="https://github.com/NullCipherr/phoa/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-1f2937?style=flat-square" alt="MIT License" /></a>
    <img src="https://img.shields.io/badge/Python-3.10%2B-0A66C2?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" />
    <img src="https://img.shields.io/badge/Interface-CLI%20%2B%20Streamlit-0EA5E9?style=flat-square" alt="CLI + Streamlit" />
  </p>
</div>

---

## Documentation

Technical documentation is organized to support onboarding, maintenance, and algorithm evolution.

- [Architecture](docs/ARCHITECTURE.md)
- [Official benchmark](docs/BENCHMARK.md)
- [Technical roadmap](ROADMAP.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

---

## Overview

**PHOA (Pride-Hunt Optimization Algorithm)** is a swarm coordination simulator with distinct drone roles for search-and-capture missions in obstacle-rich environments.

Project priorities:

- Reduce search time (`T`) without disproportionately increasing total energy (`E`).
- Coordinate the transition from exploration (scouts) to engagement (finishers).
- Ensure version-to-version comparability with deterministic seed-based benchmarks.
- Provide execution via **CLI**, a **Streamlit** dashboard, and offline telemetry export.

---

## Features

- Grid-based simulation with static and dynamic obstacles.
- Two agent roles: **Scout** (exploration) and **Finisher** (capture).
- Encirclement logic with phase-2 trigger based on heat and angular coverage.
- Static or moving target (`random_walk` and `evasive`).
- Interchangeable scout policies (`phoa` and `greedy`).
- Adaptive pursuit for dynamic scenarios.
- Official benchmark with fixed scenarios.
- Threshold grid search (`engage_threshold` and `coverage_threshold`).
- Telemetry export in `csv` or `parquet`.
- Local and containerized execution (Docker and Docker Compose).

---

## Architecture

Main execution flow:

1. `main.py` prepares the `src/` path and delegates to the CLI.
2. `src/phoa/cli.py` parses arguments and decides between simulation, benchmark, or tuning.
3. `src/phoa/simulation.py` instantiates grid, agents, and coordinator, then runs the mission loop.
4. `src/phoa/coordinator.py` applies tactical strategy (encirclement, phase transition, engagement).
5. `src/phoa/policies.py` injects scout movement policy.
6. `src/phoa/telemetry.py` persists metrics for later analysis.
7. `src/phoa/streamlit_app.py` provides real-time tactical visualization and replay.

---

## Benchmark

The official Phase 1 benchmark is documented in `docs/BENCHMARK.md` and implemented in `src/phoa/benchmark.py`.

Default scenarios:

- `baseline_urban_low_obstacles`
- `dense_obstacles`
- `wide_grid_more_scouts`

Primary metrics:

- `found`
- `search_time (T)`
- `energy_consumption (E)`
- `phase_two_step`
- `angular_coverage`
- `capture_rate`

Run benchmark:

```bash
python main.py --benchmark
```

Run comparative benchmark via module:

```bash
python -m phoa.benchmark
```

---

## Technical Stack

- **Language:** Python 3.10+
- **Visualization:** Streamlit + Plotly + Pillow
- **Quality:** Ruff + Pytest + MyPy
- **Packaging:** `pyproject.toml` with `src layout`
- **Execution:** CLI + GUI script
- **Containerization:** Docker + Docker Compose

---

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── ARCHITECTURE.md
│   └── BENCHMARK.md
├── scripts/
│   ├── run_cli.sh
│   └── run_streamlit.sh
├── src/
│   └── phoa/
│       ├── __init__.py
│       ├── benchmark.py
│       ├── cli.py
│       ├── coordinator.py
│       ├── drones.py
│       ├── policies.py
│       ├── simulation.py
│       ├── spatial_grid.py
│       ├── streamlit_app.py
│       ├── telemetry.py
│       └── tuning.py
├── tests/
│   ├── conftest.py
│   ├── test_benchmark.py
│   ├── test_coordinator.py
│   ├── test_simulation.py
│   └── test_tuning.py
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── Makefile
├── README.md
├── ROADMAP.md
├── main.py
├── pyproject.toml
├── requirements.txt
└── streamlit_app.py
```

---

## Running the Project

### Prerequisites

- Python `3.10+`
- `pip`
- Docker 24+ and Docker Compose v2 (optional)

### Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### CLI simulation

```bash
python main.py
```

Example without real-time rendering:

```bash
python main.py --no-viz --steps 200
```

Example with evasive target and adaptive pursuit:

```bash
python main.py --target-mode evasive --target-move-prob 0.45 --adaptive-pursuit
```

Example with baseline policy:

```bash
python main.py --policy greedy --target-mode random_walk --target-move-prob 0.40
```

Telemetry export:

```bash
python main.py --telemetry-output exports/run_01.csv --telemetry-format csv
```

Automatic threshold tuning:

```bash
python main.py --tune-thresholds
```

### Streamlit dashboard

```bash
streamlit run streamlit_app.py
```

---

## Docker

Build image:

```bash
docker build -t phoa:latest .
```

Run CLI simulation in container:

```bash
docker run --rm phoa:latest python main.py --no-viz --steps 120
```

Run Streamlit in container:

```bash
docker run --rm -p 8501:8501 phoa:latest \
  streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=8501
```

Docker Compose (web):

```bash
docker compose up --build phoa-web
```

Docker Compose (cli profile):

```bash
docker compose --profile cli up --build phoa-cli
```

---

## Make Targets

- `make setup`: create virtual environment and install dev dependencies.
- `make lint`: run `ruff check .`.
- `make test`: run `pytest`.
- `make run`: run default simulation.
- `make run-dynamic`: run dynamic scenario with adaptive pursuit.
- `make run-web`: start Streamlit dashboard.
- `make benchmark`: run official benchmark.
- `make tune`: run threshold grid search.
- `make docker-build`: build Docker image.
- `make docker-run-cli`: run CLI simulation in container.
- `make docker-run-web`: run Streamlit in container.
- `make docker-compose-web`: start web service via Compose.
- `make docker-compose-cli`: start CLI service via Compose profile.

---

## Quality and CI

The CI pipeline (`.github/workflows/ci.yml`) validates:

- Python `3.10`, `3.11`, and `3.12`
- Lint with `ruff`
- Tests with `pytest`

Run locally:

```bash
ruff check .
pytest
```

---

## Roadmap

Technical planning is available in [ROADMAP.md](ROADMAP.md), with evolution by phases:

- `0.1.x`: technical foundation (completed)
- `0.2.x`: algorithm quality (completed)
- `0.3.x`: simulation scalability (planned)
- `0.4.x`: advanced application (planned)

---

## License

This project is licensed under the **MIT License**.

See [LICENSE](LICENSE).

---

## Contributing

Contributions are welcome.

Before opening a PR, read [CONTRIBUTING.md](CONTRIBUTING.md) and run lint/tests locally.

<div align="center">
  Built for incremental evolution, experimental comparability, and operational clarity.
</div>

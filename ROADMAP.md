# ROADMAP - PHOA

## Vision
Evolve PHOA from a functional simulator into an applied research platform for swarm coordination in SAR and urban logistics, focused on algorithm quality, observability, and experimental reproducibility.

## Product Goals
- Improve search efficiency: reduce `T` without disproportionately increasing `E`.
- Increase operational robustness: handle dynamic obstacles and complex environments better.
- Make the project reproducible: benchmark, metrics, and experiment pipelines.
- Prepare the foundation for adoption: clear documentation, stable API, and reliable visualization.

## Phase 1 - Technical Foundation (0.1.x)
Status: completed (2026-04-06)

Deliverables:
- Consolidate modular architecture (`grid`, `agents`, `coordinator`, `simulation`).
- Strengthen test suite (unit + minimal loop integration).
- Standardize output metrics (`T`, `E`, angular coverage, capture rate).
- Publish stable Docker images for CLI and Streamlit.

Definition of done:
- Test coverage for critical algorithm paths.
- Deterministic seed-based execution in benchmark scenarios.
- CI validating lint and tests across multiple Python versions.

Evidence:
- Critical tests added for `PrideCoordinator` and deterministic benchmark behavior.
- Standardized metrics via `SimulationResult`.
- Official benchmark documented in `docs/BENCHMARK.md`.
- Operational Dockerfile and docker-compose in the repository.

## Phase 2 - Algorithm Quality (0.2.x)
Status: completed (2026-04-06)

Deliverables:
- Support for moving target with adaptive pursuit strategies.
- Interchangeable movement policy layer (baseline vs. PHOA variants).
- Automatic threshold tuning (`engage_threshold`, angular coverage) via grid search.
- CSV/Parquet telemetry logging for offline analysis.

Definition of done:
- Comparative benchmark between policies with consolidated report.
- Measurable efficiency gain in at least one standard scenario.

Evidence:
- Moving target with `random_walk` and `evasive` modes + adaptive pursuit.
- Interchangeable policies in `src/phoa/policies.py` (`phoa` and `greedy`).
- Threshold grid search in `src/phoa/tuning.py` with `--tune-thresholds` command.
- CSV/Parquet telemetry persistence with `--telemetry-output`.

## Phase 3 - Simulation Scalability (0.3.x)
Status: planned

Deliverables:
- Batch experiment engine (parameter sweeps at scale).
- Parallel scenario execution with statistical aggregation.
- Map module with urban presets (controlled density and dynamics).
- Result export for analytical dashboards.

Definition of done:
- Reproducible experiment pipeline with one consolidated report per run.
- Reduced execution time for large experiment campaigns.

## Phase 4 - Advanced Application (0.4.x)
Status: planned

Deliverables:
- Integration API for external mission input.
- More realistic energy models (hover, acceleration, sensor cost).
- Simulation of degraded communication and partial agent loss.
- Stakeholder demo mode with guided scenarios.

Definition of done:
- Failure scenarios documented and mitigated.
- Stable interface for third-party integration.

## Prioritized Backlog (next sprints)
1. Expand `PrideCoordinator` tests (phase-2 trigger and angular coverage).
2. Implement persistent telemetry module (`exports/` with CSV).
3. Add optional moving target to `SimulationConfig`.
4. Create official benchmark (`docs/benchmark.md`) with fixed scenarios.
5. Publish contribution guide for algorithmic features (technical PR template).

## Risks and Mitigations
- Overfitting to simple scenarios:
  - Mitigation: varied map and seed sets for validation.
- Growing complexity without standardization:
  - Mitigation: module contracts and layer-based testing.
- Lack of comparability between versions:
  - Mitigation: versioned benchmark and required metrics in PRs.

## Success Indicators
- Capture rate per scenario.
- Mean and standard deviation of `T` and `E`.
- Execution time per experiment campaign.
- Metric stability across versions.

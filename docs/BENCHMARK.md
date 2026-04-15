# Official Benchmark - Phase 1

## Goal
Ensure comparability between PHOA versions with fixed, deterministic seed-based scenarios.

## Official Scenarios
Defined in `src/phoa/benchmark.py`:
- `baseline_urban_low_obstacles`
- `dense_obstacles`
- `wide_grid_more_scouts`

Each scenario uses a fixed `seed` and explicit configuration for reproducibility.

## How to Run
### Via CLI
```bash
python main.py --benchmark
```

This command also prints a consolidated comparison between `phoa` and `greedy` policies.

### Via module
```bash
python -m phoa.benchmark
```

## Standardized Metrics (Phase 1)
- `found` (target capture)
- `search_time` (`T`)
- `energy_consumption` (`E`)
- `phase_two_step`
- `angular_coverage`
- `capture_rate`

## Quality Requirement
- Two consecutive runs with the same benchmark must produce identical results.
- This contract is validated in `tests/test_benchmark.py`.

## Threshold Tuning (Phase 2)
Grid search for `engage_threshold` and `coverage_threshold`:
```bash
python main.py --tune-thresholds
```

from __future__ import annotations

import itertools
import statistics
from dataclasses import dataclass

from .benchmark import DEFAULT_BENCHMARK_CASES, BenchmarkCase
from .simulation import Simulation, SimulationConfig, SimulationResult


@dataclass(frozen=True)
class TuningCandidate:
    """Resultado agregado de um ponto da grade de limiares."""

    engage_threshold: float
    coverage_threshold: float
    success_rate: float
    avg_search_time: float
    avg_energy: float
    objective_score: float


@dataclass(frozen=True)
class TuningResult:
    """Saída do grid search com melhor candidato e ranking completo."""

    best: TuningCandidate
    ranked: list[TuningCandidate]


def _evaluate_threshold_pair(
    engage_threshold: float,
    coverage_threshold: float,
    policy_name: str,
    target_mode: str,
    cases: tuple[BenchmarkCase, ...],
) -> TuningCandidate:
    results: list[SimulationResult] = []
    for case in cases:
        cfg = SimulationConfig(**vars(case.config))
        cfg.engage_threshold = engage_threshold
        cfg.min_angular_coverage = coverage_threshold
        cfg.scout_policy = policy_name
        cfg.target_mode = target_mode
        cfg.adaptive_pursuit = target_mode != "static"
        results.append(Simulation(cfg).run(visualize=False))

    success_rate = statistics.mean(r.capture_rate for r in results)
    avg_t = statistics.mean(r.search_time for r in results)
    avg_e = statistics.mean(r.energy_consumption for r in results)
    # Menor é melhor; prioriza taxa de sucesso, depois T e E.
    objective = (1.0 - success_rate) * 1_000.0 + avg_t + (avg_e * 0.01)
    return TuningCandidate(
        engage_threshold=engage_threshold,
        coverage_threshold=coverage_threshold,
        success_rate=success_rate,
        avg_search_time=avg_t,
        avg_energy=avg_e,
        objective_score=objective,
    )


def grid_search_thresholds(
    engage_values: tuple[float, ...] = (0.55, 0.60, 0.65, 0.70, 0.75),
    coverage_values: tuple[float, ...] = (0.45, 0.50, 0.55, 0.60, 0.65),
    policy_name: str = "phoa",
    target_mode: str = "evasive",
    cases: tuple[BenchmarkCase, ...] = DEFAULT_BENCHMARK_CASES,
) -> TuningResult:
    """Executa ajuste automático de limiares por grid search."""
    ranked = [
        _evaluate_threshold_pair(e, c, policy_name, target_mode, cases)
        for e, c in itertools.product(engage_values, coverage_values)
    ]
    ranked.sort(key=lambda x: x.objective_score)
    return TuningResult(best=ranked[0], ranked=ranked)


def main() -> None:
    """Entrypoint para ajuste de limiares (Fase 2)."""
    result = grid_search_thresholds()
    best = result.best
    print("=== Grid Search de Limiar (PHOA) ===")
    print(
        f"melhor engage={best.engage_threshold:.2f} coverage={best.coverage_threshold:.2f} "
        f"success_rate={best.success_rate:.2f} avg_T={best.avg_search_time:.2f} avg_E={best.avg_energy:.2f}"
    )
    print("\nTop 5 candidatos:")
    for item in result.ranked[:5]:
        print(
            f"- engage={item.engage_threshold:.2f} coverage={item.coverage_threshold:.2f} "
            f"score={item.objective_score:.2f} success={item.success_rate:.2f} "
            f"T={item.avg_search_time:.2f} E={item.avg_energy:.2f}"
        )


if __name__ == "__main__":
    main()


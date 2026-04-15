from __future__ import annotations

import statistics
from dataclasses import dataclass

from .simulation import Simulation, SimulationConfig, SimulationResult


@dataclass(frozen=True)
class BenchmarkCase:
    """Configuração nomeada de um cenário de benchmark."""

    name: str
    config: SimulationConfig


@dataclass(frozen=True)
class BenchmarkSummary:
    """Resumo estatístico agregado de um conjunto de cenários."""

    total_cases: int
    success_rate: float
    avg_search_time: float
    avg_energy: float
    avg_angular_coverage: float


@dataclass(frozen=True)
class PolicyBenchmarkSummary:
    """Resumo consolidado por política para benchmark comparativo."""

    policy_name: str
    success_rate: float
    avg_search_time: float
    avg_energy: float
    avg_angular_coverage: float


DEFAULT_BENCHMARK_CASES: tuple[BenchmarkCase, ...] = (
    BenchmarkCase(
        name="baseline_urban_low_obstacles",
        config=SimulationConfig(seed=7, steps=120, obstacle_ratio=0.08, dynamic_obstacles=3),
    ),
    BenchmarkCase(
        name="dense_obstacles",
        config=SimulationConfig(seed=17, steps=160, obstacle_ratio=0.14, dynamic_obstacles=4),
    ),
    BenchmarkCase(
        name="wide_grid_more_scouts",
        config=SimulationConfig(
            seed=23,
            width=40,
            height=24,
            scouts=8,
            finishers=2,
            steps=170,
            obstacle_ratio=0.09,
            dynamic_obstacles=5,
            target_mode="evasive",
            target_move_prob=0.45,
            adaptive_pursuit=True,
        ),
    ),
)


def run_benchmark(cases: tuple[BenchmarkCase, ...] = DEFAULT_BENCHMARK_CASES) -> list[tuple[str, SimulationResult]]:
    """Executa cenários em modo determinístico e retorna resultados por nome."""
    results: list[tuple[str, SimulationResult]] = []
    for case in cases:
        result = Simulation(case.config).run(visualize=False)
        results.append((case.name, result))
    return results


def run_policy_comparison(
    policies: tuple[str, ...] = ("phoa", "greedy"),
    cases: tuple[BenchmarkCase, ...] = DEFAULT_BENCHMARK_CASES,
) -> dict[str, list[tuple[str, SimulationResult]]]:
    """Executa benchmark para múltiplas políticas e retorna resultados por política."""
    grouped: dict[str, list[tuple[str, SimulationResult]]] = {}
    for policy in policies:
        policy_results: list[tuple[str, SimulationResult]] = []
        for case in cases:
            cfg = SimulationConfig(**vars(case.config))
            cfg.scout_policy = policy
            cfg.adaptive_pursuit = cfg.target_mode != "static"
            policy_results.append((case.name, Simulation(cfg).run(visualize=False)))
        grouped[policy] = policy_results
    return grouped


def summarize_benchmark(results: list[tuple[str, SimulationResult]]) -> BenchmarkSummary:
    """Consolida resultados em métricas médias para comparação entre versões."""
    if not results:
        return BenchmarkSummary(0, 0.0, 0.0, 0.0, 0.0)
    values = [r for _, r in results]
    return BenchmarkSummary(
        total_cases=len(values),
        success_rate=statistics.mean(r.capture_rate for r in values),
        avg_search_time=statistics.mean(r.search_time for r in values),
        avg_energy=statistics.mean(r.energy_consumption for r in values),
        avg_angular_coverage=statistics.mean(r.angular_coverage for r in values),
    )


def summarize_policy_comparison(
    grouped_results: dict[str, list[tuple[str, SimulationResult]]],
) -> list[PolicyBenchmarkSummary]:
    """Consolida resultados de múltiplas políticas em métricas comparáveis."""
    summaries: list[PolicyBenchmarkSummary] = []
    for policy_name, results in grouped_results.items():
        raw = [r for _, r in results]
        summaries.append(
            PolicyBenchmarkSummary(
                policy_name=policy_name,
                success_rate=statistics.mean(r.capture_rate for r in raw) if raw else 0.0,
                avg_search_time=statistics.mean(r.search_time for r in raw) if raw else 0.0,
                avg_energy=statistics.mean(r.energy_consumption for r in raw) if raw else 0.0,
                avg_angular_coverage=statistics.mean(r.angular_coverage for r in raw) if raw else 0.0,
            )
        )
    return sorted(summaries, key=lambda s: (-s.success_rate, s.avg_search_time, s.avg_energy))


def main() -> None:
    """Entrypoint do benchmark oficial com comparação de políticas."""
    results = run_benchmark()
    summary = summarize_benchmark(results)

    print("=== Benchmark PHOA (deterministico por seed) ===")
    for case_name, result in results:
        print(
            f"- {case_name}: found={result.found} "
            f"T={result.search_time} E={result.energy_consumption:.2f} "
            f"coverage={result.angular_coverage:.2f} phase2={result.phase_two_step}"
        )
    print(
        f"\nResumo: casos={summary.total_cases} "
        f"success_rate={summary.success_rate:.2f} "
        f"avg_T={summary.avg_search_time:.2f} "
        f"avg_E={summary.avg_energy:.2f} "
        f"avg_coverage={summary.avg_angular_coverage:.2f}"
    )

    print("\n=== Benchmark Comparativo de Politicas ===")
    for item in summarize_policy_comparison(run_policy_comparison()):
        print(
            f"- policy={item.policy_name} success_rate={item.success_rate:.2f} "
            f"avg_T={item.avg_search_time:.2f} avg_E={item.avg_energy:.2f} "
            f"avg_coverage={item.avg_angular_coverage:.2f}"
        )


if __name__ == "__main__":
    main()


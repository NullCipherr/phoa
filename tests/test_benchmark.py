from __future__ import annotations

from phoa.benchmark import run_benchmark, run_policy_comparison, summarize_policy_comparison


def test_benchmark_e_deterministico_por_seed() -> None:
    first = [(name, result.to_dict()) for name, result in run_benchmark()]
    second = [(name, result.to_dict()) for name, result in run_benchmark()]
    assert first == second


def test_benchmark_comparativo_retorna_duas_politicas() -> None:
    comparison = run_policy_comparison(policies=("phoa", "greedy"))
    assert set(comparison.keys()) == {"phoa", "greedy"}
    summaries = summarize_policy_comparison(comparison)
    assert len(summaries) == 2

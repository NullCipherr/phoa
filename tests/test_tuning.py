from __future__ import annotations

from phoa.tuning import grid_search_thresholds


def test_grid_search_retorna_melhor_candidato_dentro_da_grade() -> None:
    engage_values = (0.60, 0.70)
    coverage_values = (0.45, 0.55)
    result = grid_search_thresholds(
        engage_values=engage_values,
        coverage_values=coverage_values,
        policy_name="phoa",
        target_mode="evasive",
    )
    assert result.best.engage_threshold in engage_values
    assert result.best.coverage_threshold in coverage_values
    assert len(result.ranked) == len(engage_values) * len(coverage_values)


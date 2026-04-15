from __future__ import annotations

from phoa.simulation import Simulation, SimulationConfig


def test_simulacao_retorna_metricas_consistentes() -> None:
    config = SimulationConfig(steps=30, frame_delay=0.0, seed=7)
    sim = Simulation(config)

    result = sim.run(visualize=False)

    assert isinstance(result.found, bool)
    assert 1 <= result.search_time <= config.steps
    assert result.energy_consumption >= 0.0
    assert result.phase_two_step is None or 1 <= result.phase_two_step <= result.search_time
    assert 0.0 <= result.angular_coverage <= 1.0
    assert result.capture_rate in {0.0, 1.0}
    assert result.policy_name == "phoa"
    assert result.target_mode == "static"
    assert result.telemetry_path is None


def test_simulacao_com_alvo_movel_telemetria_csv(tmp_path) -> None:
    output = tmp_path / "telemetry.csv"
    config = SimulationConfig(
        steps=20,
        frame_delay=0.0,
        seed=13,
        target_mode="random_walk",
        target_move_prob=1.0,
        adaptive_pursuit=True,
        telemetry_output_path=str(output),
        telemetry_format="csv",
    )
    result = Simulation(config).run(visualize=False)

    assert result.target_mode == "random_walk"
    assert result.telemetry_path is not None
    assert output.exists()

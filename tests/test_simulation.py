from __future__ import annotations

from phoa.simulation import Simulation, SimulationConfig


def test_simulacao_retorna_metricas_consistentes() -> None:
    config = SimulationConfig(steps=30, frame_delay=0.0, seed=7)
    sim = Simulation(config)

    found, t, e, phase2 = sim.run(visualize=False)

    assert isinstance(found, bool)
    assert 1 <= t <= config.steps
    assert e >= 0.0
    assert phase2 is None or 1 <= phase2 <= t

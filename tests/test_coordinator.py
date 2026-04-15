from __future__ import annotations

from phoa.coordinator import PrideCoordinator
from phoa.drones import Finisher, Scout
from phoa.spatial_grid import Point, SpatialGrid


def _build_scout(drone_id: int, pos: Point) -> Scout:
    return Scout(
        drone_id=drone_id,
        pos=pos,
        speed=1,
        energy=100.0,
        move_cost=1.0,
        sensor_noise=0.05,
        role="scout",
    )


def _build_finisher(drone_id: int, pos: Point) -> Finisher:
    return Finisher(
        drone_id=drone_id,
        pos=pos,
        speed=1,
        energy=100.0,
        move_cost=1.2,
        sensor_noise=0.05,
        role="finisher",
    )


def test_transition_phase_two_depende_de_cobertura_e_calor() -> None:
    center = Point(5, 5)
    target = Point(5, 6)
    grid = SpatialGrid(width=11, height=11, obstacle_ratio=0.0, dynamic_obstacles=0, rng_seed=1)
    grid.add_heat(center, 1.0)

    scouts_baixa_cobertura = [
        _build_scout(0, Point(8, 5)),
        _build_scout(1, Point(8, 6)),
        _build_scout(2, Point(7, 6)),
        _build_scout(3, Point(8, 4)),
    ]
    finisher = _build_finisher(100, Point(1, 1))
    coord = PrideCoordinator(
        grid=grid,
        scouts=scouts_baixa_cobertura,
        finishers=[finisher],
        target=target,
        rng_seed=2,
        engage_threshold=0.7,
        min_angular_coverage=0.55,
    )
    transitioned = coord.TransitionToPhaseTwo(step=1)
    assert transitioned is False
    assert finisher.engaged is False

    scouts_alta_cobertura = [
        _build_scout(10, Point(8, 5)),
        _build_scout(11, Point(5, 8)),
        _build_scout(12, Point(2, 5)),
        _build_scout(13, Point(5, 2)),
    ]
    finisher2 = _build_finisher(101, Point(1, 1))
    coord2 = PrideCoordinator(
        grid=grid,
        scouts=scouts_alta_cobertura,
        finishers=[finisher2],
        target=target,
        rng_seed=3,
        engage_threshold=0.7,
        min_angular_coverage=0.55,
    )
    transitioned2 = coord2.TransitionToPhaseTwo(step=2)
    assert transitioned2 is True
    assert finisher2.engaged is True


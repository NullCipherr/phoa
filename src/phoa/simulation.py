from __future__ import annotations

import time
from dataclasses import dataclass

from .coordinator import PrideCoordinator
from .drones import Finisher, Scout
from .spatial_grid import SpatialGrid


@dataclass
class SimulationConfig:
    width: int = 32
    height: int = 18
    scouts: int = 6
    finishers: int = 2
    steps: int = 120
    seed: int = 7
    obstacle_ratio: float = 0.08
    dynamic_obstacles: int = 3
    frame_delay: float = 0.05
    engage_threshold: float = 0.65
    min_angular_coverage: float = 0.50


class Simulation:
    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.grid = SpatialGrid(
            width=config.width,
            height=config.height,
            obstacle_ratio=config.obstacle_ratio,
            dynamic_obstacles=config.dynamic_obstacles,
            rng_seed=config.seed,
        )
        self.target = self.grid.random_free_point()
        scout_list: list[Scout] = []
        for i in range(config.scouts):
            scout_list.append(
                Scout(
                    drone_id=i,
                    pos=self.grid.random_free_point(),
                    speed=1,
                    energy=100.0,
                    move_cost=0.95,
                    sensor_noise=0.12,
                    role="scout",
                )
            )
        finisher_list: list[Finisher] = []
        for j in range(config.finishers):
            finisher_list.append(
                Finisher(
                    drone_id=100 + j,
                    pos=self.grid.random_free_point(),
                    speed=2,
                    energy=140.0,
                    move_cost=1.6,
                    sensor_noise=0.05,
                    role="finisher",
                )
            )
        self.coordinator = PrideCoordinator(
            grid=self.grid,
            scouts=scout_list,
            finishers=finisher_list,
            target=self.target,
            rng_seed=config.seed + 11,
            engage_threshold=config.engage_threshold,
            min_angular_coverage=config.min_angular_coverage,
        )

    def _render(self, step_idx: int) -> str:
        canvas = [["." for _ in range(self.config.width)] for _ in range(self.config.height)]
        for obs in self.grid.obstacles:
            canvas[obs.y][obs.x] = "#"
        canvas[self.target.y][self.target.x] = "T"

        for s in self.coordinator.scouts:
            canvas[s.pos.y][s.pos.x] = "S"
        for f in self.coordinator.finishers:
            canvas[f.pos.y][f.pos.x] = "F" if f.engaged else "f"

        center = self.grid.best_heat_point()
        if canvas[center.y][center.x] == ".":
            canvas[center.y][center.x] = "H"

        lines = ["".join(row) for row in canvas]
        m = self.coordinator.metrics(step_idx)
        status = "PHASE-2" if self.coordinator.phase_two else "PHASE-1"
        header = (
            f"step={step_idx:03d} status={status} "
            f"max_heat={self.grid.max_heat():.2f} "
            f"E_spent={m.total_energy_spent:.2f} "
            f"T={step_idx}"
        )
        return header + "\n" + "\n".join(lines)

    def render_frame(self, step_idx: int) -> str:
        return self._render(step_idx)

    def run(self, visualize: bool = True) -> tuple[bool, int, float, int | None]:
        found = False
        steps_taken = 0
        for step_idx in range(1, self.config.steps + 1):
            self.coordinator.step(step_idx)
            steps_taken = step_idx
            if visualize:
                print("\033[H\033[J", end="")
                print(self._render(step_idx))
                time.sleep(self.config.frame_delay)
            if self.coordinator.target_captured():
                found = True
                break
        m = self.coordinator.metrics(steps_taken)
        return found, steps_taken, m.total_energy_spent, m.phase_two_step

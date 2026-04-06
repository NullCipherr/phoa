from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .spatial_grid import Point, SpatialGrid


@dataclass
class Drone:
    drone_id: int
    pos: Point
    speed: int
    energy: float
    move_cost: float
    sensor_noise: float
    role: str
    path: list[Point] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.path.append(self.pos)

    def distance(self, target: Point) -> float:
        return math.hypot(target.x - self.pos.x, target.y - self.pos.y)

    def can_move(self) -> bool:
        return self.energy >= self.move_cost

    def move_towards(self, grid: SpatialGrid, target: Point) -> None:
        if not self.can_move():
            return
        for _ in range(self.speed):
            nbrs = grid.neighbor_points(self.pos)
            if not nbrs:
                return
            best = min(nbrs, key=lambda p: math.hypot(target.x - p.x, target.y - p.y))
            self.pos = best
            self.energy -= self.move_cost
            self.path.append(self.pos)
            grid.mark_visit(self.pos)

    def move_to(self, grid: SpatialGrid, next_pos: Point) -> None:
        if not self.can_move():
            return
        if next_pos in grid.neighbor_points(self.pos):
            self.pos = next_pos
            self.energy -= self.move_cost
            self.path.append(self.pos)
            grid.mark_visit(self.pos)


@dataclass
class Scout(Drone):
    explore_bias: float = 0.65

    def scan_target_signal(self, target: Point, rng: random.Random) -> float:
        """
        Sinal probabilístico inversamente proporcional à distância, com ruído.
        P ~ exp(-d / sigma) + N(0, sensor_noise)
        """
        d = self.distance(target)
        sigma = 5.0
        clean = math.exp(-d / sigma)
        noisy = clean + rng.gauss(0.0, self.sensor_noise)
        return max(0.0, min(1.0, noisy))

    def explore_step(self, grid: SpatialGrid, target_hint: Point, rng: random.Random) -> None:
        if not self.can_move():
            return
        nbrs = grid.neighbor_points(self.pos)
        if not nbrs:
            return
        def score(p: Point) -> float:
            explore = grid.uncertainty_score(p)
            towards_hint = 1.0 / (1.0 + math.hypot(target_hint.x - p.x, target_hint.y - p.y))
            jitter = rng.random() * 0.05
            return self.explore_bias * explore + (1.0 - self.explore_bias) * towards_hint + jitter

        best = max(nbrs, key=score)
        self.move_to(grid, best)


@dataclass
class Finisher(Drone):
    standby_cost: float = 0.02
    engaged: bool = False

    def standby_step(self) -> None:
        self.energy = max(0.0, self.energy - self.standby_cost)


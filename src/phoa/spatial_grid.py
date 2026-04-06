from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: int
    y: int


class SpatialGrid:
    """
    Ambiente discreto 2D com:
    - célula livre/ocupada,
    - mapa de calor probabilístico do alvo,
    - obstáculos dinâmicos.
    """

    def __init__(
        self,
        width: int,
        height: int,
        obstacle_ratio: float = 0.08,
        dynamic_obstacles: int = 3,
        rng_seed: int | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self.rng = random.Random(rng_seed)
        self.dynamic_obstacles = dynamic_obstacles
        self.obstacles: set[Point] = set()
        self.heat_map = [[0.0 for _ in range(width)] for _ in range(height)]
        self.visits = [[0 for _ in range(width)] for _ in range(height)]
        self._spawn_static_obstacles(obstacle_ratio)

    def _spawn_static_obstacles(self, ratio: float) -> None:
        n_cells = self.width * self.height
        n_obstacles = int(n_cells * ratio)
        while len(self.obstacles) < n_obstacles:
            p = Point(self.rng.randrange(self.width), self.rng.randrange(self.height))
            self.obstacles.add(p)

    def in_bounds(self, p: Point) -> bool:
        return 0 <= p.x < self.width and 0 <= p.y < self.height

    def is_free(self, p: Point) -> bool:
        return self.in_bounds(p) and p not in self.obstacles

    def random_free_point(self) -> Point:
        while True:
            p = Point(self.rng.randrange(self.width), self.rng.randrange(self.height))
            if self.is_free(p):
                return p

    def neighbor_points(self, p: Point) -> list[Point]:
        candidates = [
            Point(p.x + 1, p.y),
            Point(p.x - 1, p.y),
            Point(p.x, p.y + 1),
            Point(p.x, p.y - 1),
            Point(p.x + 1, p.y + 1),
            Point(p.x - 1, p.y - 1),
            Point(p.x + 1, p.y - 1),
            Point(p.x - 1, p.y + 1),
        ]
        return [c for c in candidates if self.is_free(c)]

    def update_dynamic_obstacles(self, protected: set[Point]) -> None:
        """
        Obstáculos dinâmicos são deslocados aleatoriamente para simular tráfego urbano.
        Células protegidas impedem "teleporte" sobre agentes/alvo.
        """
        if self.dynamic_obstacles <= 0 or not self.obstacles:
            return
        movable = list(self.obstacles)
        self.rng.shuffle(movable)
        moved = 0
        for old in movable:
            if moved >= self.dynamic_obstacles:
                break
            if old in protected:
                continue
            nbrs = self.neighbor_points(old)
            self.rng.shuffle(nbrs)
            for new in nbrs:
                if new in self.obstacles or new in protected:
                    continue
                self.obstacles.remove(old)
                self.obstacles.add(new)
                moved += 1
                break

    def add_heat(self, p: Point, value: float) -> None:
        if not self.in_bounds(p):
            return
        self.heat_map[p.y][p.x] = max(0.0, self.heat_map[p.y][p.x] + value)

    def diffuse_heat(self, decay: float = 0.96) -> None:
        """
        Difusão local do mapa de calor:
        H_{t+1}(i,j) = decay * [0.5*H_t(i,j) + 0.5*mean(vizinhos)]
        """
        new_map = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                p = Point(x, y)
                if p in self.obstacles:
                    continue
                nbrs = self.neighbor_points(p)
                if not nbrs:
                    local_mean = self.heat_map[y][x]
                else:
                    local_mean = sum(self.heat_map[n.y][n.x] for n in nbrs) / len(nbrs)
                new_map[y][x] = decay * (0.5 * self.heat_map[y][x] + 0.5 * local_mean)
        self.heat_map = new_map

    def mark_visit(self, p: Point) -> None:
        if self.in_bounds(p):
            self.visits[p.y][p.x] += 1

    def uncertainty_score(self, p: Point) -> float:
        """
        Quanto menor o número de visitas, maior o incentivo para explorar.
        """
        if not self.in_bounds(p):
            return -1e9
        return 1.0 / (1 + self.visits[p.y][p.x])

    def best_heat_point(self) -> Point:
        best = Point(0, 0)
        best_v = -1.0
        for y in range(self.height):
            for x in range(self.width):
                p = Point(x, y)
                if p in self.obstacles:
                    continue
                v = self.heat_map[y][x]
                if v > best_v:
                    best_v = v
                    best = p
        return best

    def max_heat(self) -> float:
        return max(max(row) for row in self.heat_map)


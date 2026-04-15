from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Protocol

from .drones import Scout
from .spatial_grid import Point, SpatialGrid


class ScoutMovementPolicy(Protocol):
    """Contrato de política de movimento para scouts."""

    name: str

    def choose_next_position(
        self,
        scout: Scout,
        grid: SpatialGrid,
        target_hint: Point,
        rng: random.Random,
    ) -> Point | None:
        """Escolhe próxima célula do scout; `None` significa permanecer."""


@dataclass(frozen=True)
class PhoaExplorationPolicy:
    """Política padrão PHOA: exploração por incerteza + atração por pista."""

    name: str = "phoa"

    def choose_next_position(
        self,
        scout: Scout,
        grid: SpatialGrid,
        target_hint: Point,
        rng: random.Random,
    ) -> Point | None:
        nbrs = grid.neighbor_points(scout.pos)
        if not nbrs:
            return None

        def score(p: Point) -> float:
            explore = grid.uncertainty_score(p)
            toward_hint = 1.0 / (1.0 + math.hypot(target_hint.x - p.x, target_hint.y - p.y))
            jitter = rng.random() * 0.05
            return scout.explore_bias * explore + (1.0 - scout.explore_bias) * toward_hint + jitter

        return max(nbrs, key=score)


@dataclass(frozen=True)
class GreedyPursuitPolicy:
    """Baseline de comparação: prioriza aproximação direta da pista."""

    name: str = "greedy"
    exploration_weight: float = 0.20

    def choose_next_position(
        self,
        scout: Scout,
        grid: SpatialGrid,
        target_hint: Point,
        rng: random.Random,
    ) -> Point | None:
        nbrs = grid.neighbor_points(scout.pos)
        if not nbrs:
            return None

        def score(p: Point) -> float:
            toward_hint = 1.0 / (1.0 + math.hypot(target_hint.x - p.x, target_hint.y - p.y))
            explore = grid.uncertainty_score(p)
            jitter = rng.random() * 0.02
            return (1.0 - self.exploration_weight) * toward_hint + self.exploration_weight * explore + jitter

        return max(nbrs, key=score)


def build_policy(policy_name: str) -> ScoutMovementPolicy:
    """Factory simples para seleção de política por nome."""
    normalized = policy_name.strip().lower()
    if normalized == "phoa":
        return PhoaExplorationPolicy()
    if normalized == "greedy":
        return GreedyPursuitPolicy()
    raise ValueError(f"Politica desconhecida: {policy_name}")


from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .drones import Finisher, Scout
from .policies import PhoaExplorationPolicy, ScoutMovementPolicy
from .spatial_grid import Point, SpatialGrid


@dataclass
class Metrics:
    """Métricas operacionais por passo da simulação."""

    step: int
    total_energy_spent: float
    phase_two_step: int | None
    found: bool
    angular_coverage: float
    capture_rate: float


@dataclass
class TacticalSnapshot:
    """Snapshot tático para visualização e telemetria detalhada."""

    step: int
    center: Point
    center_heat: float
    max_heat: float
    angular_coverage: float
    avg_scout_distance_to_target: float
    avg_finisher_distance_to_target: float
    engaged_finishers: int


class PrideCoordinator:
    """
    Coordena o PHOA em duas fases:
    1) Batedores exploram e formam cerco.
    2) Finalizadores engajam quando probabilidade e geometria do cerco forem suficientes.
    """

    def __init__(
        self,
        grid: SpatialGrid,
        scouts: list[Scout],
        finishers: list[Finisher],
        target: Point,
        rng_seed: int | None = None,
        engage_threshold: float = 0.68,
        min_angular_coverage: float = 0.55,
        scout_policy: ScoutMovementPolicy | None = None,
        adaptive_pursuit: bool = False,
    ) -> None:
        self.grid = grid
        self.scouts = scouts
        self.finishers = finishers
        self.target = target
        self.prev_target = target
        self.target_velocity = (0, 0)
        self.rng = random.Random(rng_seed)
        self.engage_threshold = engage_threshold
        self.min_angular_coverage = min_angular_coverage
        self.scout_policy = scout_policy or PhoaExplorationPolicy()
        self.adaptive_pursuit = adaptive_pursuit
        self.phase_two = False
        self.phase_two_step: int | None = None
        self.total_initial_energy = sum(d.energy for d in scouts + finishers)

    def _bearing(self, p: Point, c: Point) -> float:
        """Ângulo polar de `p` em relação ao centro `c`."""
        return math.atan2(p.y - c.y, p.x - c.x)

    def _angular_coverage(self, center: Point) -> float:
        """
        Cobertura angular do cerco:
        - Cada scout ocupa um ângulo theta_i em torno do centro.
        - Ordenamos os ângulos e calculamos o maior gap (lacuna) circular.
        - Cobertura = 1 - (maior_gap / 2pi)
        """
        if len(self.scouts) < 2:
            return 0.0
        angles = sorted(self._bearing(s.pos, center) for s in self.scouts)
        gaps = []
        for i in range(len(angles)):
            a = angles[i]
            b = angles[(i + 1) % len(angles)]
            gap = (b - a) % (2 * math.pi)
            gaps.append(gap)
        max_gap = max(gaps)
        return max(0.0, 1.0 - (max_gap / (2 * math.pi)))

    def _centroid(self, points: list[Point]) -> Point:
        x = round(sum(p.x for p in points) / len(points))
        y = round(sum(p.y for p in points) / len(points))
        return Point(x, y)

    def _encirclement_center(self) -> Point:
        """Centro tático atual definido pelo pico do heatmap."""
        return self.grid.best_heat_point()

    def update_target_state(self, new_target: Point) -> None:
        """Atualiza alvo e estima velocidade discreta para perseguição adaptativa."""
        vx = new_target.x - self.target.x
        vy = new_target.y - self.target.y
        self.prev_target = self.target
        self.target = new_target
        self.target_velocity = (vx, vy)

    def CoordinateEncirclement(self) -> None:
        """
        Scouts formam um cerco adaptativo ao redor do centro de calor.

        Lógica geométrica:
        - Definimos um centro C (máximo do heat map).
        - Para N batedores, o ângulo ideal do i-ésimo scout é phi_i = 2*pi*i/N.
        - Cada scout busca deslocamento que minimize:
          J = w_r * |r_i - r*| + w_t * |Delta_theta_i|
          onde:
          r_i = distância ao centro,
          r*  = raio desejado (proporcional ao tamanho do mapa),
          Delta_theta_i = diferença angular ao setor ideal.
        """
        center = self._encirclement_center()
        n = len(self.scouts)
        if n == 0:
            return
        desired_radius = max(2.0, min(self.grid.width, self.grid.height) * 0.14)
        wr, wt = 0.55, 0.45

        for i, scout in enumerate(sorted(self.scouts, key=lambda s: s.drone_id)):
            phi_i = (2 * math.pi * i) / n
            nbrs = self.grid.neighbor_points(scout.pos)
            if not nbrs:
                continue
            best = scout.pos
            best_cost = float("inf")
            for cand in nbrs:
                dx = cand.x - center.x
                dy = cand.y - center.y
                r_i = math.hypot(dx, dy)
                theta = math.atan2(dy, dx)
                dtheta = abs((theta - phi_i + math.pi) % (2 * math.pi) - math.pi)
                cost = wr * abs(r_i - desired_radius) + wt * dtheta
                cost += self.rng.random() * 0.03
                if cost < best_cost:
                    best = cand
                    best_cost = cost
            scout.move_to(self.grid, best)

    def TransitionToPhaseTwo(self, step: int) -> bool:
        """Ativa finalizadores quando calor e cobertura angular atingem limiares."""
        center = self._encirclement_center()
        heat = self.grid.heat_map[center.y][center.x]
        coverage = self._angular_coverage(center)
        trigger = heat >= self.engage_threshold and coverage >= self.min_angular_coverage
        if trigger and not self.phase_two:
            self.phase_two = True
            self.phase_two_step = step
            for fin in self.finishers:
                fin.engaged = True
        return self.phase_two

    def update_scouts(self) -> None:
        """Atualiza exploração e contribuição de calor dos scouts."""
        hint = self._encirclement_center()
        for scout in self.scouts:
            next_pos = self.scout_policy.choose_next_position(scout, self.grid, hint, self.rng)
            if next_pos is not None:
                scout.move_to(self.grid, next_pos)
            signal = scout.scan_target_signal(self.target, self.rng)
            self.grid.add_heat(scout.pos, signal * 0.7)
            if scout.distance(self.target) <= 1.5:
                self.grid.add_heat(self.target, 1.0)

    def update_finishers(self) -> None:
        """Atualiza estado dos finishers (standby ou avanço para centro)."""
        center = self._encirclement_center()
        predicted_target = self.target
        if self.adaptive_pursuit:
            vx, vy = self.target_velocity
            predicted = Point(self.target.x + vx, self.target.y + vy)
            if self.grid.is_free(predicted):
                predicted_target = predicted
        for fin in self.finishers:
            if not fin.engaged:
                fin.standby_step()
                continue
            pursuit_point = predicted_target if self.adaptive_pursuit else center
            fin.move_towards(self.grid, pursuit_point)

    def target_captured(self) -> bool:
        """Verifica captura do alvo por proximidade de ao menos um finisher."""
        for fin in self.finishers:
            if fin.distance(self.target) <= 1.0:
                return True
        return False

    def step(self, step_idx: int) -> None:
        """Executa um ciclo completo de atualização do sistema PHOA."""
        protected = {self.target}
        protected.update(s.pos for s in self.scouts)
        protected.update(f.pos for f in self.finishers)
        self.grid.update_dynamic_obstacles(protected=protected)
        self.grid.diffuse_heat()
        self.update_scouts()
        self.CoordinateEncirclement()
        self.TransitionToPhaseTwo(step_idx)
        self.update_finishers()

    def metrics(self, step_idx: int) -> Metrics:
        """Calcula métricas agregadas usadas por CLI, testes e benchmark."""
        remaining = sum(d.energy for d in self.scouts + self.finishers)
        spent = self.total_initial_energy - remaining
        center = self._encirclement_center()
        coverage = self._angular_coverage(center)
        found = self.target_captured()
        return Metrics(
            step=step_idx,
            total_energy_spent=spent,
            phase_two_step=self.phase_two_step,
            found=found,
            angular_coverage=coverage,
            capture_rate=1.0 if found else 0.0,
        )

    def tactical_snapshot(self, step_idx: int) -> TacticalSnapshot:
        """Coleta estado tático detalhado para frontend e análise."""
        center = self._encirclement_center()
        center_heat = self.grid.heat_map[center.y][center.x]
        coverage = self._angular_coverage(center)
        avg_scout_distance = (
            sum(s.distance(self.target) for s in self.scouts) / len(self.scouts) if self.scouts else 0.0
        )
        avg_finisher_distance = (
            sum(f.distance(self.target) for f in self.finishers) / len(self.finishers) if self.finishers else 0.0
        )
        engaged_finishers = sum(1 for f in self.finishers if f.engaged)
        return TacticalSnapshot(
            step=step_idx,
            center=center,
            center_heat=center_heat,
            max_heat=self.grid.max_heat(),
            angular_coverage=coverage,
            avg_scout_distance_to_target=avg_scout_distance,
            avg_finisher_distance_to_target=avg_finisher_distance,
            engaged_finishers=engaged_finishers,
        )

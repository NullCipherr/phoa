from __future__ import annotations

import random
import time
from dataclasses import dataclass

from .coordinator import PrideCoordinator
from .drones import Finisher, Scout
from .policies import build_policy
from .spatial_grid import SpatialGrid
from .telemetry import TelemetryRecord, export_telemetry


@dataclass(frozen=True)
class SimulationResult:
    """Contrato de saída padronizado da simulação PHOA."""

    found: bool
    search_time: int
    energy_consumption: float
    phase_two_step: int | None
    angular_coverage: float
    capture_rate: float
    policy_name: str
    target_mode: str
    telemetry_path: str | None

    def __iter__(self):
        """
        Compatibilidade retroativa para desempacotamento legado:
        found, t, e, phase2 = sim.run(...)
        """
        yield self.found
        yield self.search_time
        yield self.energy_consumption
        yield self.phase_two_step

    def to_dict(self) -> dict[str, float | int | bool | None]:
        """Serializa resultado para formato estável usado por testes/benchmark."""
        return {
            "found": self.found,
            "search_time": self.search_time,
            "energy_consumption": round(self.energy_consumption, 6),
            "phase_two_step": self.phase_two_step,
            "angular_coverage": round(self.angular_coverage, 6),
            "capture_rate": round(self.capture_rate, 6),
            "policy_name": self.policy_name,
            "target_mode": self.target_mode,
            "telemetry_path": self.telemetry_path,
        }


@dataclass
class SimulationConfig:
    """Parâmetros de execução da simulação."""

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
    target_mode: str = "static"
    target_move_prob: float = 0.35
    scout_policy: str = "phoa"
    adaptive_pursuit: bool = False
    telemetry_output_path: str | None = None
    telemetry_format: str = "csv"


class Simulation:
    """Orquestra ciclo completo de simulação e coleta de métricas."""

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.rng = random.Random(config.seed + 101)
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
            scout_policy=build_policy(config.scout_policy),
            adaptive_pursuit=config.adaptive_pursuit,
        )
        self.telemetry_records: list[TelemetryRecord] = []

    def _move_target(self) -> None:
        """Move alvo opcionalmente para cenários dinâmicos."""
        mode = self.config.target_mode.lower()
        if mode == "static":
            return
        if self.rng.random() > self.config.target_move_prob:
            return

        candidates = self.grid.neighbor_points(self.target)
        if not candidates:
            return

        occupied = {s.pos for s in self.coordinator.scouts}
        occupied.update(f.pos for f in self.coordinator.finishers)
        candidates = [c for c in candidates if c not in occupied]
        if not candidates:
            return

        if mode == "random_walk":
            new_target = self.rng.choice(candidates)
        elif mode == "evasive":
            centroid_x = sum(s.pos.x for s in self.coordinator.scouts) / max(1, len(self.coordinator.scouts))
            centroid_y = sum(s.pos.y for s in self.coordinator.scouts) / max(1, len(self.coordinator.scouts))
            new_target = max(candidates, key=lambda p: (p.x - centroid_x) ** 2 + (p.y - centroid_y) ** 2)
        else:
            raise ValueError(f"Modo de alvo desconhecido: {self.config.target_mode}")

        self.target = new_target
        self.coordinator.update_target_state(new_target)

    def _append_telemetry(self, step_idx: int) -> None:
        metrics = self.coordinator.metrics(step_idx)
        tactical = self.coordinator.tactical_snapshot(step_idx)
        self.telemetry_records.append(
            TelemetryRecord(
                step=step_idx,
                found=metrics.found,
                phase_two=self.coordinator.phase_two,
                phase_two_step=metrics.phase_two_step,
                total_energy_spent=metrics.total_energy_spent,
                angular_coverage=metrics.angular_coverage,
                max_heat=tactical.max_heat,
                center_heat=tactical.center_heat,
                target_x=self.target.x,
                target_y=self.target.y,
                engaged_finishers=tactical.engaged_finishers,
            )
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
        """Renderiza frame textual (ASCII) para debug e CLI."""
        return self._render(step_idx)

    def run(self, visualize: bool = True) -> SimulationResult:
        """
        Executa o loop principal até captura ou horizonte máximo.

        Args:
            visualize: Se `True`, imprime evolução passo a passo no terminal.
        """
        found = False
        steps_taken = 0
        for step_idx in range(1, self.config.steps + 1):
            self._move_target()
            self.coordinator.step(step_idx)
            steps_taken = step_idx
            self._append_telemetry(step_idx)
            if visualize:
                print("\033[H\033[J", end="")
                print(self._render(step_idx))
                time.sleep(self.config.frame_delay)
            if self.coordinator.target_captured():
                found = True
                break
        m = self.coordinator.metrics(steps_taken)
        tactical = self.coordinator.tactical_snapshot(steps_taken)
        telemetry_path: str | None = None
        if self.config.telemetry_output_path:
            telemetry_path = export_telemetry(
                self.telemetry_records,
                output_path=self.config.telemetry_output_path,
                file_format=self.config.telemetry_format,
            )
        return SimulationResult(
            found=found,
            search_time=steps_taken,
            energy_consumption=m.total_energy_spent,
            phase_two_step=m.phase_two_step,
            angular_coverage=tactical.angular_coverage,
            capture_rate=1.0 if found else 0.0,
            policy_name=self.config.scout_policy,
            target_mode=self.config.target_mode,
            telemetry_path=telemetry_path,
        )

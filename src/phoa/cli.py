from __future__ import annotations

import argparse

from .benchmark import main as run_benchmark_main
from .simulation import Simulation, SimulationConfig
from .tuning import main as run_tuning_main


def parse_args() -> argparse.Namespace:
    """Define e retorna os argumentos da CLI do PHOA."""
    parser = argparse.ArgumentParser(
        description="PHOA - Pride-Hunt Optimization Algorithm (SAR/Logistica Urbana)"
    )
    parser.add_argument("--width", type=int, default=32)
    parser.add_argument("--height", type=int, default=18)
    parser.add_argument("--scouts", type=int, default=6)
    parser.add_argument("--finishers", type=int, default=2)
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--obstacle-ratio", type=float, default=0.08)
    parser.add_argument("--dynamic-obstacles", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--no-viz", action="store_true", help="Desabilita visualizacao em tempo real.")
    parser.add_argument("--engage-threshold", type=float, default=0.65)
    parser.add_argument("--coverage-threshold", type=float, default=0.50)
    parser.add_argument("--target-mode", choices=["static", "random_walk", "evasive"], default="static")
    parser.add_argument("--target-move-prob", type=float, default=0.35)
    parser.add_argument("--policy", choices=["phoa", "greedy"], default="phoa")
    parser.add_argument("--adaptive-pursuit", action="store_true")
    parser.add_argument("--telemetry-output", type=str, default=None)
    parser.add_argument("--telemetry-format", choices=["csv", "parquet"], default="csv")
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Executa benchmark deterministico oficial da Fase 1.",
    )
    parser.add_argument(
        "--tune-thresholds",
        action="store_true",
        help="Executa grid search para ajuste de limiares de fase 2.",
    )
    return parser.parse_args()


def main() -> None:
    """Executa simulação única ou benchmark oficial conforme argumentos."""
    args = parse_args()
    if args.benchmark:
        run_benchmark_main()
        return
    if args.tune_thresholds:
        run_tuning_main()
        return
    config = SimulationConfig(
        width=args.width,
        height=args.height,
        scouts=args.scouts,
        finishers=args.finishers,
        steps=args.steps,
        seed=args.seed,
        obstacle_ratio=args.obstacle_ratio,
        dynamic_obstacles=args.dynamic_obstacles,
        frame_delay=args.delay,
        engage_threshold=args.engage_threshold,
        min_angular_coverage=args.coverage_threshold,
        target_mode=args.target_mode,
        target_move_prob=args.target_move_prob,
        scout_policy=args.policy,
        adaptive_pursuit=args.adaptive_pursuit,
        telemetry_output_path=args.telemetry_output,
        telemetry_format=args.telemetry_format,
    )
    result = Simulation(config).run(visualize=not args.no_viz)
    print("\n=== Resultado PHOA ===")
    print(f"Alvo capturado: {'sim' if result.found else 'nao'}")
    print(f"Search Time (T): {result.search_time}")
    print(f"Energy Consumption (E): {result.energy_consumption:.2f}")
    print(f"Cobertura Angular: {result.angular_coverage:.2f}")
    print(f"Taxa de Captura: {result.capture_rate:.2f}")
    print(f"Politica: {result.policy_name}")
    print(f"Modo do Alvo: {result.target_mode}")
    if result.telemetry_path:
        print(f"Telemetria: {result.telemetry_path}")
    print(f"Transicao para Fase 2: {result.phase_two_step if result.phase_two_step is not None else 'nao ocorreu'}")


if __name__ == "__main__":
    main()

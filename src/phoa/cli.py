from __future__ import annotations

import argparse

from .simulation import Simulation, SimulationConfig


def parse_args() -> argparse.Namespace:
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
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
    )
    sim = Simulation(config)
    found, t, e, phase2 = sim.run(visualize=not args.no_viz)
    print("\n=== Resultado PHOA ===")
    print(f"Alvo capturado: {'sim' if found else 'nao'}")
    print(f"Search Time (T): {t}")
    print(f"Energy Consumption (E): {e:.2f}")
    print(f"Transicao para Fase 2: {phase2 if phase2 is not None else 'nao ocorreu'}")


if __name__ == "__main__":
    main()

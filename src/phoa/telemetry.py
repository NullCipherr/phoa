from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class TelemetryRecord:
    """Registro temporal para análise offline de comportamento da simulação."""

    step: int
    found: bool
    phase_two: bool
    phase_two_step: int | None
    total_energy_spent: float
    angular_coverage: float
    max_heat: float
    center_heat: float
    target_x: int
    target_y: int
    engaged_finishers: int


def export_telemetry(records: list[TelemetryRecord], output_path: str, file_format: str = "csv") -> str:
    """Exporta telemetria para CSV ou Parquet e retorna caminho absoluto."""
    if not records:
        raise ValueError("Nao ha registros para exportar telemetria.")

    fmt = file_format.strip().lower()
    if fmt not in {"csv", "parquet"}:
        raise ValueError(f"Formato de telemetria nao suportado: {file_format}")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = [asdict(r) for r in records]
    if fmt == "csv":
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    else:
        pd.DataFrame(rows).to_parquet(path, index=False)

    return str(path.resolve())


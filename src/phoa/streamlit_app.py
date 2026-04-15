from __future__ import annotations

import time
from dataclasses import dataclass
from io import BytesIO

import plotly.graph_objects as go
import streamlit as st
from PIL import Image, ImageDraw
from plotly.subplots import make_subplots

from .simulation import Simulation, SimulationConfig


@dataclass(frozen=True)
class PursuitFrame:
    """Snapshot visual mínimo necessário para renderização do GIF da perseguição."""

    step_idx: int
    phase: str
    total_energy_spent: float
    max_heat: float
    angular_coverage: float
    heat_map: list[list[float]]
    obstacles: list[tuple[int, int]]
    scouts: list[tuple[int, int]]
    finishers: list[tuple[int, int, bool]]
    target: tuple[int, int]
    center: tuple[int, int]


def render_dashboard_header() -> None:
    st.markdown(
        """
        <section class="phoa-hero">
          <div class="phoa-hero__badge">PHOA • Tactical Dashboard</div>
          <h1 class="phoa-hero__title">Console de Coordenação e Perseguição</h1>
          <p class="phoa-hero__subtitle">
            Visualização operacional da missão com mapa tático, telemetria em tempo real e replay consolidado em GIF.
          </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_cards(
    *,
    phase: str,
    step_idx: int,
    energy_spent: float,
    max_heat: float,
    angular_coverage: float,
    engaged_finishers: int,
) -> None:
    cards = [
        ("Fase", phase),
        ("Search Time (T)", str(step_idx)),
        ("Energy (E)", f"{energy_spent:.2f}"),
        ("Heat Máx", f"{max_heat:.2f}"),
        ("Cobertura Angular", f"{angular_coverage:.2f}"),
        ("Finishers Engajados", str(engaged_finishers)),
    ]
    cols = st.columns(6, gap="small")
    for col, (label, value) in zip(cols, cards, strict=True):
        col.markdown(
            f"""
            <article class="phoa-kpi-card">
              <p class="phoa-kpi-card__label">{label}</p>
              <p class="phoa-kpi-card__value">{value}</p>
            </article>
            """,
            unsafe_allow_html=True,
        )


def render_result_cards(
    *,
    found: bool,
    steps_taken: int,
    energy_consumption: float,
    phase_two_step: int | None,
) -> None:
    cards = [
        ("Alvo capturado", "sim" if found else "não"),
        ("Search Time (T)", str(steps_taken)),
        ("Energy Consumption (E)", f"{energy_consumption:.2f}"),
        ("Transição fase 2", str(phase_two_step) if phase_two_step is not None else "N/A"),
    ]
    cols = st.columns(4, gap="small")
    for col, (label, value) in zip(cols, cards, strict=True):
        col.markdown(
            f"""
            <article class="phoa-kpi-card phoa-kpi-card--result">
              <p class="phoa-kpi-card__label">{label}</p>
              <p class="phoa-kpi-card__value">{value}</p>
            </article>
            """,
            unsafe_allow_html=True,
        )


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    color = hex_color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _lerp_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
    )


def _sample_heat_color(norm_value: float) -> tuple[int, int, int]:
    stops: list[tuple[float, tuple[int, int, int]]] = [
        (0.00, _hex_to_rgb("#0b132b")),
        (0.20, _hex_to_rgb("#1c2541")),
        (0.45, _hex_to_rgb("#3a506b")),
        (0.70, _hex_to_rgb("#5bc0be")),
        (1.00, _hex_to_rgb("#f4d35e")),
    ]
    v = max(0.0, min(1.0, norm_value))
    for idx in range(1, len(stops)):
        left_pos, left_color = stops[idx - 1]
        right_pos, right_color = stops[idx]
        if v <= right_pos:
            span = max(1e-9, right_pos - left_pos)
            return _lerp_color(left_color, right_color, (v - left_pos) / span)
    return stops[-1][1]


def build_pursuit_frame(
    sim: Simulation,
    *,
    step_idx: int,
    phase: str,
    total_energy_spent: float,
    max_heat: float,
    angular_coverage: float,
) -> PursuitFrame:
    snapshot = sim.coordinator.tactical_snapshot(step_idx)
    return PursuitFrame(
        step_idx=step_idx,
        phase=phase,
        total_energy_spent=total_energy_spent,
        max_heat=max_heat,
        angular_coverage=angular_coverage,
        heat_map=[row[:] for row in sim.grid.heat_map],
        obstacles=[(o.x, o.y) for o in sim.grid.obstacles],
        scouts=[(s.pos.x, s.pos.y) for s in sim.coordinator.scouts],
        finishers=[(f.pos.x, f.pos.y, f.engaged) for f in sim.coordinator.finishers],
        target=(sim.coordinator.target.x, sim.coordinator.target.y),
        center=(snapshot.center.x, snapshot.center.y),
    )


def build_pursuit_gif(frames: list[PursuitFrame], config: SimulationConfig) -> bytes | None:
    if not frames:
        return None

    max_frames = 180
    stride = max(1, len(frames) // max_frames)
    selected = frames[::stride]
    if selected[-1].step_idx != frames[-1].step_idx:
        selected.append(frames[-1])

    cell_px = max(12, min(22, 820 // max(config.width, config.height)))
    legend_width = 210
    header_height = 54
    padding = 16
    grid_w = config.width * cell_px
    grid_h = config.height * cell_px
    canvas_w = grid_w + legend_width + (padding * 3)
    canvas_h = grid_h + header_height + (padding * 2)

    max_heat_value = max(1e-6, max(frame.max_heat for frame in selected))
    rendered_frames: list[Image.Image] = []

    for frame in selected:
        image = Image.new("RGB", (canvas_w, canvas_h), "#020617")
        draw = ImageDraw.Draw(image)

        draw.rectangle([(0, 0), (canvas_w, header_height)], fill="#0f172a")
        draw.text(
            (padding, 12),
            (
                f"PHOA Pursuit Replay | Step {frame.step_idx}/{config.steps} | {frame.phase} | "
                f"E={frame.total_energy_spent:.2f} | Cobertura={frame.angular_coverage:.2f}"
            ),
            fill="#f8fafc",
        )

        left = padding
        top = header_height + padding

        for y in range(config.height):
            for x in range(config.width):
                x0 = left + (x * cell_px)
                y0 = top + (y * cell_px)
                x1 = x0 + cell_px - 1
                y1 = y0 + cell_px - 1
                norm = frame.heat_map[y][x] / max_heat_value
                draw.rectangle([(x0, y0), (x1, y1)], fill=_sample_heat_color(norm))

        for ox, oy in frame.obstacles:
            x0 = left + (ox * cell_px)
            y0 = top + (oy * cell_px)
            x1 = x0 + cell_px - 1
            y1 = y0 + cell_px - 1
            draw.rectangle([(x0, y0), (x1, y1)], fill="#0b0b0b")

        for sx, sy in frame.scouts:
            cx = left + sx * cell_px + (cell_px / 2)
            cy = top + sy * cell_px + (cell_px / 2)
            r = max(3, cell_px * 0.30)
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill="#50e3c2", outline="#062b23", width=1)

        for fx, fy, engaged in frame.finishers:
            cx = left + fx * cell_px + (cell_px / 2)
            cy = top + fy * cell_px + (cell_px / 2)
            r = max(3, cell_px * 0.34)
            color = "#ff8f00" if engaged else "#ffd166"
            diamond = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
            draw.polygon(diamond, fill=color, outline="#3f2b00")

        tx, ty = frame.target
        tx0 = left + tx * cell_px
        ty0 = top + ty * cell_px
        tx1 = tx0 + cell_px - 1
        ty1 = ty0 + cell_px - 1
        pad = max(2, round(cell_px * 0.25))
        draw.line([(tx0 + pad, ty0 + pad), (tx1 - pad, ty1 - pad)], fill="#ff4d6d", width=max(2, cell_px // 7))
        draw.line([(tx1 - pad, ty0 + pad), (tx0 + pad, ty1 - pad)], fill="#ff4d6d", width=max(2, cell_px // 7))

        cx, cy = frame.center
        cx0 = left + cx * cell_px + (cell_px / 2)
        cy0 = top + cy * cell_px + (cell_px / 2)
        cross_size = max(3, round(cell_px * 0.33))
        draw.line([(cx0 - cross_size, cy0), (cx0 + cross_size, cy0)], fill="#f4d35e", width=max(2, cell_px // 8))
        draw.line([(cx0, cy0 - cross_size), (cx0, cy0 + cross_size)], fill="#f4d35e", width=max(2, cell_px // 8))

        legend_x = left + grid_w + padding
        legend_y = top
        draw.text((legend_x, legend_y), "Legenda", fill="#e2e8f0")
        legend_items = [
            ("Scout", "#50e3c2"),
            ("Finisher standby", "#ffd166"),
            ("Finisher engajado", "#ff8f00"),
            ("Alvo", "#ff4d6d"),
            ("Centro do cerco", "#f4d35e"),
            ("Obstáculo", "#0b0b0b"),
        ]
        for idx, (label, color) in enumerate(legend_items):
            y = legend_y + 28 + idx * 24
            draw.rectangle([(legend_x, y), (legend_x + 16, y + 16)], fill=color)
            draw.text((legend_x + 22, y), label, fill="#cbd5e1")

        rendered_frames.append(image)

    output = BytesIO()
    frame_duration_ms = max(90, int(config.frame_delay * 1800))
    rendered_frames[0].save(
        output,
        format="GIF",
        append_images=rendered_frames[1:],
        save_all=True,
        duration=frame_duration_ms,
        loop=0,
        optimize=True,
    )
    output.seek(0)
    return output.getvalue()


def build_battlefield_figure(sim: Simulation, show_trails: bool, trail_window: int) -> go.Figure:
    grid = sim.grid
    coord = sim.coordinator
    snapshot = coord.tactical_snapshot(step_idx=0)

    fig = go.Figure()
    fig.add_trace(
        go.Heatmap(
            z=grid.heat_map,
            colorscale=[
                [0.0, "#0b132b"],
                [0.20, "#1c2541"],
                [0.45, "#3a506b"],
                [0.70, "#5bc0be"],
                [1.0, "#f4d35e"],
            ],
            showscale=True,
            colorbar={"title": "Heat"},
            zmin=0.0,
            zmax=max(1.0, grid.max_heat()),
            hovertemplate="x=%{x}, y=%{y}, heat=%{z:.2f}<extra></extra>",
        )
    )

    obs_x = [o.x for o in grid.obstacles]
    obs_y = [o.y for o in grid.obstacles]
    fig.add_trace(
        go.Scatter(
            x=obs_x,
            y=obs_y,
            mode="markers",
            marker={"symbol": "square", "size": 9, "color": "#111111", "line": {"width": 0}},
            name="Obstáculos",
            hovertemplate="Obstáculo: x=%{x}, y=%{y}<extra></extra>",
        )
    )

    if show_trails:
        for scout in coord.scouts:
            points = scout.path[-trail_window:]
            fig.add_trace(
                go.Scatter(
                    x=[p.x for p in points],
                    y=[p.y for p in points],
                    mode="lines",
                    line={"width": 2, "color": "rgba(80, 227, 194, 0.35)"},
                    name=f"Trilha Scout {scout.drone_id}",
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
        for fin in coord.finishers:
            points = fin.path[-trail_window:]
            fig.add_trace(
                go.Scatter(
                    x=[p.x for p in points],
                    y=[p.y for p in points],
                    mode="lines",
                    line={"width": 2, "color": "rgba(248, 150, 30, 0.35)"},
                    name=f"Trilha Finisher {fin.drone_id}",
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    fig.add_trace(
        go.Scatter(
            x=[s.pos.x for s in coord.scouts],
            y=[s.pos.y for s in coord.scouts],
            mode="markers",
            marker={"size": 12, "color": "#50e3c2", "line": {"width": 1, "color": "#0b0f1a"}},
            name="Scouts",
            hovertemplate="Scout: x=%{x}, y=%{y}<extra></extra>",
        )
    )

    engaged = [f for f in coord.finishers if f.engaged]
    standby = [f for f in coord.finishers if not f.engaged]
    if standby:
        fig.add_trace(
            go.Scatter(
                x=[f.pos.x for f in standby],
                y=[f.pos.y for f in standby],
                mode="markers",
                marker={"size": 14, "color": "#ffd166", "symbol": "diamond", "line": {"width": 1, "color": "#222"}},
                name="Finishers (standby)",
                hovertemplate="Finisher standby: x=%{x}, y=%{y}<extra></extra>",
            )
        )
    if engaged:
        fig.add_trace(
            go.Scatter(
                x=[f.pos.x for f in engaged],
                y=[f.pos.y for f in engaged],
                mode="markers",
                marker={"size": 14, "color": "#ff8f00", "symbol": "diamond", "line": {"width": 1, "color": "#222"}},
                name="Finishers (engajados)",
                hovertemplate="Finisher engajado: x=%{x}, y=%{y}<extra></extra>",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[coord.target.x],
            y=[coord.target.y],
            mode="markers",
            marker={"size": 15, "color": "#ff4d6d", "symbol": "x", "line": {"width": 2, "color": "#550014"}},
            name="Alvo",
            hovertemplate="Alvo: x=%{x}, y=%{y}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[snapshot.center.x],
            y=[snapshot.center.y],
            mode="markers",
            marker={"size": 12, "color": "#f4d35e", "symbol": "cross", "line": {"width": 1, "color": "#705c00"}},
            name="Centro de Cerco",
            hovertemplate="Centro: x=%{x}, y=%{y}<extra></extra>",
        )
    )

    fig.update_layout(
        height=620,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        legend={"orientation": "h", "y": -0.08},
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font={"color": "#e2e8f0"},
    )
    fig.update_xaxes(title="Eixo X", range=[-0.5, grid.width - 0.5], dtick=1, showgrid=False, zeroline=False)
    fig.update_yaxes(
        title="Eixo Y",
        range=[grid.height - 0.5, -0.5],
        dtick=1,
        showgrid=False,
        zeroline=False,
        scaleanchor="x",
        scaleratio=1,
    )
    return fig


def build_telemetry_figure(
    steps: list[int],
    energy_spent: list[float],
    max_heat: list[float],
    angular_coverage: list[float],
) -> go.Figure:
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.18,
        row_heights=[0.44, 0.56],
    )
    fig.add_trace(
        go.Scatter(
            x=steps,
            y=energy_spent,
            mode="lines",
            name="Energia gasta (E)",
            line={"width": 3, "color": "#ff8f00"},
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=steps,
            y=max_heat,
            mode="lines",
            name="Heat máx",
            line={"width": 3, "color": "#5bc0be"},
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=steps,
            y=angular_coverage,
            mode="lines",
            name="Cobertura angular",
            line={"width": 3, "color": "#f4d35e"},
        ),
        row=2,
        col=1,
    )
    fig.update_layout(
        height=460,
        margin={"l": 12, "r": 12, "t": 16, "b": 16},
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font={"color": "#e2e8f0"},
        legend={"orientation": "h", "y": -0.22},
    )
    fig.update_xaxes(title_text="Passos", row=2, col=1, title_standoff=10)
    fig.update_yaxes(title_text="Energia", row=1, col=1, title_standoff=8)
    fig.update_yaxes(title_text="Heat / Cobertura", row=2, col=1, title_standoff=8)
    return fig


def run_streamlit_simulation(config: SimulationConfig, realtime: bool, show_trails: bool, trail_window: int) -> None:
    sim = Simulation(config)

    kpi_row = st.empty()
    progress = st.progress(0, text="Inicializando simulação...")
    left, right = st.columns([1.6, 1.0], gap="large")
    left_panel = left.container(border=True)
    right_panel = right.container(border=True)
    left_panel.markdown('<h3 class="phoa-section-title">Mapa Tático</h3>', unsafe_allow_html=True)
    right_panel.markdown('<h3 class="phoa-section-title">Telemetria da Missão</h3>', unsafe_allow_html=True)
    battlefield_box = left_panel.empty()
    telemetry_box = right_panel.empty()
    replay_box = st.empty()

    history_steps: list[int] = []
    history_energy: list[float] = []
    history_heat: list[float] = []
    history_coverage: list[float] = []
    pursuit_frames: list[PursuitFrame] = []

    found = False
    steps_taken = 0

    for step_idx in range(1, config.steps + 1):
        sim.coordinator.step(step_idx)
        steps_taken = step_idx

        metrics = sim.coordinator.metrics(step_idx)
        snapshot = sim.coordinator.tactical_snapshot(step_idx)
        phase = "PHASE-2" if sim.coordinator.phase_two else "PHASE-1"

        history_steps.append(step_idx)
        history_energy.append(metrics.total_energy_spent)
        history_heat.append(snapshot.max_heat)
        history_coverage.append(snapshot.angular_coverage)
        pursuit_frames.append(
            build_pursuit_frame(
                sim,
                step_idx=step_idx,
                phase=phase,
                total_energy_spent=metrics.total_energy_spent,
                max_heat=snapshot.max_heat,
                angular_coverage=snapshot.angular_coverage,
            )
        )

        with kpi_row.container():
            st.markdown('<section class="phoa-kpi-strip">', unsafe_allow_html=True)
            render_kpi_cards(
                phase=phase,
                step_idx=step_idx,
                energy_spent=metrics.total_energy_spent,
                max_heat=snapshot.max_heat,
                angular_coverage=snapshot.angular_coverage,
                engaged_finishers=snapshot.engaged_finishers,
            )
            st.markdown("</section>", unsafe_allow_html=True)

        battlefield_box.plotly_chart(
            build_battlefield_figure(sim, show_trails=show_trails, trail_window=trail_window),
            width="stretch",
            key=f"battlefield_{step_idx}",
        )
        telemetry_box.plotly_chart(
            build_telemetry_figure(history_steps, history_energy, history_heat, history_coverage),
            width="stretch",
            key=f"telemetry_{step_idx}",
        )

        progress.progress(int((step_idx / config.steps) * 100), text=f"Passo {step_idx}/{config.steps}")

        if sim.coordinator.target_captured():
            found = True
            break
        if realtime:
            time.sleep(config.frame_delay)

    final_metrics = sim.coordinator.metrics(steps_taken)
    st.markdown('<div class="phoa-section-gap"></div>', unsafe_allow_html=True)
    result_panel = st.container(border=True)
    result_panel.markdown('<h3 class="phoa-section-title">Resultado Final</h3>', unsafe_allow_html=True)
    with result_panel:
        render_result_cards(
            found=found,
            steps_taken=steps_taken,
            energy_consumption=final_metrics.total_energy_spent,
            phase_two_step=final_metrics.phase_two_step,
        )

    st.markdown('<div class="phoa-section-gap"></div>', unsafe_allow_html=True)
    with replay_box.container():
        replay_panel = st.container(border=True)
        replay_panel.markdown('<h3 class="phoa-section-title">Replay da Perseguição (GIF)</h3>', unsafe_allow_html=True)
        replay_gif = build_pursuit_gif(pursuit_frames, config)
        if replay_gif is not None:
            replay_panel.image(replay_gif, caption="Animação consolidada da perseguição", width="stretch")
            replay_panel.download_button(
                "Baixar GIF da perseguição",
                data=replay_gif,
                file_name=f"phoa_pursuit_seed_{config.seed}.gif",
                mime="image/gif",
                width="stretch",
            )


def main() -> None:
    st.set_page_config(page_title="PHOA Tactical Console", layout="wide")
    st.markdown(
        """
        <style>
        :root {
          --phoa-bg: #020617;
          --phoa-surface: #0b1222;
          --phoa-surface-soft: #131c31;
          --phoa-border: #1f2c4d;
          --phoa-text: #e2e8f0;
          --phoa-muted: #94a3b8;
          --phoa-accent: #5bc0be;
          --phoa-accent-2: #f4d35e;
        }
        .stApp {
          background:
            radial-gradient(circle at 8% 2%, rgba(91, 192, 190, 0.20) 0%, rgba(2, 6, 23, 0) 28%),
            radial-gradient(circle at 95% 8%, rgba(244, 211, 94, 0.12) 0%, rgba(2, 6, 23, 0) 24%),
            linear-gradient(180deg, #050b17 0%, #020617 40%, #020617 100%);
          color: var(--phoa-text);
        }
        h1, h2, h3, p, label, div { color: var(--phoa-text); }
        [data-testid="stSidebar"] {
          background: linear-gradient(180deg, #0a1324 0%, #08101d 100%);
          border-right: 1px solid var(--phoa-border);
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
          border: 1px solid var(--phoa-border);
          border-radius: 14px;
          background: linear-gradient(180deg, rgba(19, 28, 49, 0.94) 0%, rgba(11, 18, 34, 0.94) 100%);
          box-shadow: 0 14px 28px rgba(0, 0, 0, 0.30);
        }
        .phoa-hero {
          padding: 18px 18px 14px 18px;
          border: 1px solid var(--phoa-border);
          border-radius: 14px;
          background:
            linear-gradient(120deg, rgba(91, 192, 190, 0.18) 0%, rgba(11, 18, 34, 0.95) 45%),
            linear-gradient(180deg, rgba(19, 28, 49, 0.96) 0%, rgba(11, 18, 34, 0.96) 100%);
          margin-bottom: 0.75rem;
        }
        .phoa-hero__badge {
          display: inline-block;
          font-size: 0.78rem;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          color: #07101f;
          background: linear-gradient(90deg, var(--phoa-accent), var(--phoa-accent-2));
          border-radius: 999px;
          padding: 0.22rem 0.7rem;
          font-weight: 700;
          margin-bottom: 0.4rem;
        }
        .phoa-hero__title {
          margin: 0 0 0.2rem 0 !important;
          font-size: 1.75rem;
          line-height: 1.2;
          font-weight: 700;
          color: #f8fafc;
        }
        .phoa-hero__subtitle {
          margin: 0;
          color: #cbd5e1;
          max-width: 840px;
        }
        .phoa-section-title {
          margin: 0.1rem 0 0.7rem 0 !important;
          font-size: 1.06rem;
          font-weight: 700;
          color: #f8fafc;
          position: relative;
          padding-left: 0.9rem;
          line-height: 1.3;
        }
        .phoa-section-title::before {
          content: "";
          position: absolute;
          left: 0;
          top: 50%;
          transform: translateY(-50%);
          width: 3px;
          height: 0.95em;
          border-radius: 3px;
          background: linear-gradient(180deg, var(--phoa-accent), var(--phoa-accent-2));
        }
        .phoa-kpi-strip { margin-bottom: 0.25rem; }
        .phoa-section-gap { height: 0.6rem; }
        .phoa-kpi-card {
          border: 1px solid var(--phoa-border);
          border-radius: 12px;
          background: linear-gradient(180deg, #111b32 0%, #0d1527 100%);
          padding: 0.62rem 0.70rem;
          min-height: 84px;
        }
        .phoa-kpi-card__label {
          margin: 0;
          font-size: 0.76rem;
          color: var(--phoa-muted);
          text-transform: uppercase;
          letter-spacing: 0.02em;
          font-weight: 600;
        }
        .phoa-kpi-card__value {
          margin: 0.28rem 0 0 0;
          font-size: 1.06rem;
          color: #f8fafc;
          font-weight: 700;
          line-height: 1.2;
        }
        .phoa-kpi-card--result .phoa-kpi-card__value { color: #f4d35e; }
        #MainMenu { visibility: hidden; }
        header { visibility: hidden; }
        [data-testid="stToolbar"] { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    render_dashboard_header()

    with st.sidebar:
        st.header("Parâmetros")
        width = st.slider("Largura do grid", min_value=20, max_value=80, value=32, step=1)
        height = st.slider("Altura do grid", min_value=12, max_value=40, value=18, step=1)
        scouts = st.slider("Scouts", min_value=2, max_value=20, value=6, step=1)
        finishers = st.slider("Finishers", min_value=1, max_value=8, value=2, step=1)
        steps = st.slider("Passos máximos", min_value=20, max_value=400, value=120, step=10)
        seed = st.number_input("Seed", min_value=0, max_value=999999, value=7, step=1)
        obstacle_ratio = st.slider("Taxa de obstáculos", min_value=0.0, max_value=0.30, value=0.08, step=0.01)
        dynamic_obstacles = st.slider("Obstáculos dinâmicos por passo", min_value=0, max_value=12, value=3, step=1)
        engage_threshold = st.slider("Limiar de engajamento", min_value=0.10, max_value=1.00, value=0.65, step=0.01)
        coverage_threshold = st.slider("Cobertura angular mínima", min_value=0.10, max_value=1.00, value=0.50, step=0.01)
        target_mode = st.selectbox("Modo do alvo", options=["static", "random_walk", "evasive"], index=0)
        target_move_prob = st.slider("Probabilidade de movimento do alvo", min_value=0.0, max_value=1.0, value=0.35, step=0.05)
        scout_policy = st.selectbox("Política dos scouts", options=["phoa", "greedy"], index=0)
        adaptive_pursuit = st.toggle("Perseguição adaptativa", value=False)
        frame_delay = st.slider("Delay entre frames (s)", min_value=0.00, max_value=0.30, value=0.05, step=0.01)
        realtime = st.toggle("Executar em tempo real", value=True)
        show_trails = st.toggle("Exibir trilhas dos drones", value=True)
        trail_window = st.slider("Janela da trilha", min_value=5, max_value=80, value=18, step=1)

    config = SimulationConfig(
        width=width,
        height=height,
        scouts=scouts,
        finishers=finishers,
        steps=steps,
        seed=int(seed),
        obstacle_ratio=obstacle_ratio,
        dynamic_obstacles=dynamic_obstacles,
        frame_delay=frame_delay,
        engage_threshold=engage_threshold,
        min_angular_coverage=coverage_threshold,
        target_mode=target_mode,
        target_move_prob=target_move_prob,
        scout_policy=scout_policy,
        adaptive_pursuit=adaptive_pursuit,
    )

    st.caption(
        "Visual tático com camadas: heat map, obstáculos, agentes, alvo e centro de cerco. "
        "A telemetria mostra evolução de energia, calor e cobertura angular para análise de eficiência."
    )

    if st.button("Iniciar Simulação", type="primary", width="stretch"):
        run_streamlit_simulation(
            config,
            realtime=realtime,
            show_trails=show_trails,
            trail_window=trail_window,
        )


if __name__ == "__main__":
    main()

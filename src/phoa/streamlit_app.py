from __future__ import annotations

import time

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from .simulation import Simulation, SimulationConfig


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
        vertical_spacing=0.14,
        subplot_titles=("Eficiência de Busca", "Confiança de Cerco"),
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
        height=420,
        margin={"l": 10, "r": 10, "t": 45, "b": 10},
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font={"color": "#e2e8f0"},
        legend={"orientation": "h", "y": -0.18},
    )
    fig.update_xaxes(title="Passos")
    fig.update_yaxes(title="Energia", row=1, col=1)
    fig.update_yaxes(title="Heat / Cobertura", row=2, col=1)
    return fig


def run_streamlit_simulation(config: SimulationConfig, realtime: bool, show_trails: bool, trail_window: int) -> None:
    sim = Simulation(config)

    kpi_row = st.empty()
    progress = st.progress(0, text="Inicializando simulação...")
    left, right = st.columns([1.6, 1.0], gap="large")
    battlefield_box = left.empty()
    telemetry_box = right.empty()

    history_steps: list[int] = []
    history_energy: list[float] = []
    history_heat: list[float] = []
    history_coverage: list[float] = []

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

        with kpi_row.container():
            k1, k2, k3, k4, k5, k6 = st.columns(6)
            k1.metric("Fase", phase)
            k2.metric("Search Time (T)", step_idx)
            k3.metric("Energy (E)", f"{metrics.total_energy_spent:.2f}")
            k4.metric("Heat Máx", f"{snapshot.max_heat:.2f}")
            k5.metric("Cobertura Angular", f"{snapshot.angular_coverage:.2f}")
            k6.metric("Finishers Engajados", snapshot.engaged_finishers)

        battlefield_box.plotly_chart(
            build_battlefield_figure(sim, show_trails=show_trails, trail_window=trail_window),
            use_container_width=True,
            key=f"battlefield_{step_idx}",
        )
        telemetry_box.plotly_chart(
            build_telemetry_figure(history_steps, history_energy, history_heat, history_coverage),
            use_container_width=True,
            key=f"telemetry_{step_idx}",
        )

        progress.progress(int((step_idx / config.steps) * 100), text=f"Passo {step_idx}/{config.steps}")

        if sim.coordinator.target_captured():
            found = True
            break
        if realtime:
            time.sleep(config.frame_delay)

    final_metrics = sim.coordinator.metrics(steps_taken)
    st.subheader("Resultado final")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Alvo capturado", "sim" if found else "não")
    c2.metric("Search Time (T)", steps_taken)
    c3.metric("Energy Consumption (E)", f"{final_metrics.total_energy_spent:.2f}")
    c4.metric("Transição fase 2", final_metrics.phase_two_step if final_metrics.phase_two_step is not None else "N/A")


def main() -> None:
    st.set_page_config(page_title="PHOA Tactical Console", layout="wide")
    st.markdown(
        """
        <style>
        .stApp { background: radial-gradient(circle at top left, #0f172a 0%, #020617 55%, #020617 100%); }
        h1, h2, h3, p, label, div { color: #e2e8f0; }
        [data-testid="stMetricLabel"] { color: #94a3b8; }
        [data-testid="stMetricValue"] { color: #f8fafc; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("PHOA Tactical Console")
    st.caption("Monitoramento visual de coordenação de drones para SAR e logística urbana.")

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
    )

    st.markdown(
        "Visual tático com camadas: heat map, obstáculos, agentes, alvo e centro de cerco. "
        "A telemetria mostra evolução de energia, calor e cobertura angular para análise de eficiência."
    )

    if st.button("Iniciar Simulação", type="primary", use_container_width=True):
        run_streamlit_simulation(
            config,
            realtime=realtime,
            show_trails=show_trails,
            trail_window=trail_window,
        )


if __name__ == "__main__":
    main()

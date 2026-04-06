# PHOA - Pride-Hunt Optimization Algorithm

Implementacao em Python de um algoritmo bioinspirado para coordenacao de drones em cenarios de Search and Rescue (SAR) e logistica urbana.

## Objetivo
- Minimizar o tempo de busca (`T`).
- Balancear o consumo de energia total (`E`).
- Coordenar agentes com papeis distintos:
  - `Scouts (Batedores)`: exploracao, reducao de incerteza e mapa de calor.
  - `Finishers (Finalizadores)`: engajamento de precisao apos confianca de cerco.

## Estrutura do projeto

```text
.
├── .github/workflows/ci.yml
├── docs/
│   └── ARCHITECTURE.md
├── scripts/
│   ├── run_cli.sh
│   └── run_streamlit.sh
├── src/phoa/
│   ├── __init__.py
│   ├── cli.py
│   ├── coordinator.py
│   ├── drones.py
│   ├── simulation.py
│   ├── spatial_grid.py
│   └── streamlit_app.py
├── tests/
│   ├── conftest.py
│   └── test_simulation.py
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── Makefile
├── main.py
├── pyproject.toml
├── requirements.txt
└── streamlit_app.py
```

## Como executar

### 1. Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 2. Simulacao CLI
```bash
python main.py
```

Exemplo sem visualizacao:
```bash
python main.py --no-viz --steps 200
```

### 3. Frontend Streamlit
```bash
streamlit run streamlit_app.py
```

## Execucao com Docker

### Build da imagem
```bash
docker build -t phoa:latest .
```

### Simulacao CLI (container)
```bash
docker run --rm phoa:latest python main.py --no-viz --steps 120
```

### Frontend Streamlit (container)
```bash
docker run --rm -p 8501:8501 phoa:latest \
  streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=8501
```

### Docker Compose
```bash
docker compose up --build phoa-web
```

Servico CLI com profile:
```bash
docker compose --profile cli up --build phoa-cli
```

## Comandos de qualidade
```bash
ruff check .
pytest
```

Ou via `Makefile`:
```bash
make setup
make lint
make test
make run
make run-web
make docker-build
make docker-run-cli
make docker-run-web
make docker-compose-web
make docker-compose-cli
```

## Logica de cerco (resumo)
No metodo `CoordinateEncirclement()`:
- Define-se o centro `C` como pico do mapa de calor.
- Cada scout recebe setor angular ideal `phi_i = 2*pi*i/N`.
- O movimento minimiza custo radial-angular:
  - `J = w_r * |r_i - r*| + w_t * |Delta_theta_i|`.

No metodo `TransitionToPhaseTwo()`:
- Finalizadores engajam quando:
  - `heat(center) >= engage_threshold`
  - `angular_coverage >= min_angular_coverage`

## Documentacao complementar
- Arquitetura: `docs/ARCHITECTURE.md`
- Contribuicao: `CONTRIBUTING.md`
- Historico de releases: `CHANGELOG.md`

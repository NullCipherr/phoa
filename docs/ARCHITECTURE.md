# Arquitetura do Projeto

## Visao geral
O projeto segue separacao entre dominio de simulacao e interfaces de execucao.

## Camadas
- `src/phoa/spatial_grid.py`: modelagem espacial e dinamica de obstaculos.
- `src/phoa/drones.py`: entidades de dominio (`Drone`, `Scout`, `Finisher`).
- `src/phoa/coordinator.py`: orquestracao tatico-operacional do PHOA.
- `src/phoa/simulation.py`: ciclo de simulacao e metricas agregadas.
- `src/phoa/cli.py`: entrypoint de linha de comando.
- `src/phoa/streamlit_app.py`: frontend para monitoramento visual.

## Decisoes arquiteturais
- Modelo orientado a objetos para papéis de agentes.
- Separacao de UI (CLI/Streamlit) do núcleo algorítmico.
- `src layout` para melhorar empacotamento, testes e distribuicao.

## Evolucao recomendada
- Introduzir camada `services/` para cenarios de experimento batch.
- Adicionar interfaces de persistencia para telemetria (CSV/Parquet/DB).
- Criar modulo de planners para substituicao de estrategias de movimento.

# Contribuindo

## Setup rapido
1. Crie ambiente virtual: `python -m venv .venv`
2. Ative o ambiente: `source .venv/bin/activate`
3. Instale dependencias de desenvolvimento: `pip install -e .[dev]`

## Fluxo recomendado
1. Crie branch a partir de `main`.
2. Rode qualidade local antes de abrir PR:
   - `ruff check .`
   - `pytest`
3. Garanta que README e docs estejam atualizados quando houver mudanca de comportamento.

## Padroes
- Código e documentação em pt-BR.
- Prefira mudanças pequenas e com objetivo claro.
- Evite acoplar lógica de simulação com camada visual.

## Pull Request
- Descreva o problema e a solução.
- Inclua evidências de teste.
- Destaque riscos e decisões arquiteturais.

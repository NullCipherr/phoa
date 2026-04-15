# Contributing

## Quick Setup
1. Create a virtual environment: `python -m venv .venv`
2. Activate it: `source .venv/bin/activate`
3. Install development dependencies: `pip install -e .[dev]`

## Recommended Workflow
1. Create a branch from `main`.
2. Run local quality checks before opening a PR:
   - `ruff check .`
   - `pytest`
3. Keep README and docs updated when behavior changes.

## Standards
- Keep code and documentation in English.
- Prefer small, focused changes.
- Avoid coupling simulation logic to the visual layer.

## Pull Request
- Describe the problem and the solution.
- Include test evidence.
- Highlight risks and architectural decisions.

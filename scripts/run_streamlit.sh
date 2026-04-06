#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".venv" ]]; then
  echo "Ambiente .venv nao encontrado. Rode: make setup"
  exit 1
fi

.venv/bin/streamlit run streamlit_app.py "$@"


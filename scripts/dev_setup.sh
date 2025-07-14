#!/bin/bash

############################################################################
# Setup desenvolvimento para PagBank Multi-Agent System
# Usage: ./scripts/dev_setup.sh
############################################################################

CURR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname $CURR_DIR)"
VENV_DIR="${REPO_ROOT}/.venv"
source ${CURR_DIR}/_utils.sh

print_heading "Configuração do ambiente de desenvolvimento PagBank..."

print_heading "Removendo ambiente virtual existente"
print_info "rm -rf ${VENV_DIR}"
rm -rf ${VENV_DIR}

print_heading "Criando novo ambiente virtual"
print_info "VIRTUAL_ENV=${VENV_DIR} uv venv --python 3.12"
VIRTUAL_ENV=${VENV_DIR} uv venv --python 3.12

print_heading "Instalando dependências"
print_info "VIRTUAL_ENV=${VENV_DIR} uv sync"
VIRTUAL_ENV=${VENV_DIR} uv sync

print_heading "Instalando workspace em modo editável"
print_info "VIRTUAL_ENV=${VENV_DIR} uv pip install -e ${REPO_ROOT}"
VIRTUAL_ENV=${VENV_DIR} uv pip install -e ${REPO_ROOT}

print_heading "Configuração completa!"
print_heading "Ative o ambiente com: source .venv/bin/activate"
print_heading "Inicie o playground com: uv run python api/playground.py"
#!/usr/bin/env bash
# Servidor MCP do CortexDB para o Claude Code (registrado em .mcp.json).
set -euo pipefail
source "$(dirname "$0")/comum.sh"
exigir_binarios
mkdir -p "$DADOS"
isolado "CORTEXDB_PATH=$DADOS/cortexdb.db" "$BIN/cortexdb-mcp"

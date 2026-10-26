#!/usr/bin/env bash
# Servidor MCP do xerj para o Claude Code (registrado em .mcp.json).
# Sobe o nó do xerj se ele ainda não estiver no ar.
set -euo pipefail
source "$(dirname "$0")/comum.sh"
exigir_binarios
"$RAIZ/scripts/subir_xerj.sh" >&2
isolado "XERJ_URL=$XERJ_URL" "XERJ_AUTH=ApiKey $(cat "$DADOS/xerj/admin.key")" "$BIN/xerj" mcp

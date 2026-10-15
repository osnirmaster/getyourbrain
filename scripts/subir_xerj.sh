#!/usr/bin/env bash
# Sobe o nó do xerj COM autenticação (sem --insecure) e indexa os repositórios/pastas passados.
# Uso: scripts/subir_xerj.sh ~/repos/servico-pix ~/repos/servico-ted ~/docs/regras
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
XERJ_BIN="${XERJ_BIN:-$HOME/.local/bin/xerj}"
XERJ_URL="${XERJ_URL:-http://localhost:9200}"
DATA_DIR="${XERJ_DATA_DIR:-$RAIZ/dados/xerj}"
mkdir -p "$DATA_DIR"

# Qualquer resposta HTTP (inclusive 401) significa que o nó já está no ar.
if [ "$(curl -s -o /dev/null -w '%{http_code}' "$XERJ_URL" || true)" = "000" ]; then
  echo "Iniciando xerj em $XERJ_URL (dados em $DATA_DIR)..."
  nohup "$XERJ_BIN" --data-dir "$DATA_DIR" > "$DATA_DIR/xerj.log" 2>&1 &
  for _ in $(seq 1 30); do
    [ -s "$DATA_DIR/admin.key" ] && break
    sleep 1
  done
fi

[ -s "$DATA_DIR/admin.key" ] || { echo "admin.key não encontrado em $DATA_DIR; veja $DATA_DIR/xerj.log" >&2; exit 1; }
export XERJ_API_KEY="$(cat "$DATA_DIR/admin.key")"

for pasta in "$@"; do
  echo "Indexando $pasta..."
  "$XERJ_BIN" autoindex "$pasta"
done
echo "Pronto."

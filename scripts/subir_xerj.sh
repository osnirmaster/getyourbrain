#!/usr/bin/env bash
# Sobe o nó do xerj COM autenticação, só em 127.0.0.1 e sem rede externa, e indexa as pastas passadas.
# Uso: scripts/subir_xerj.sh ~/repos/servico-pix ~/repos/servico-ted ~/docs/regras
set -euo pipefail
source "$(dirname "$0")/comum.sh"
exigir_binarios
DATA_DIR="$DADOS/xerj"
mkdir -p "$DATA_DIR"

# Qualquer resposta HTTP (inclusive 401) significa que o nó já está no ar.
if [ "$(curl -s -o /dev/null -w '%{http_code}' "$XERJ_URL" || true)" = "000" ]; then
  echo "Iniciando xerj em $XERJ_URL (dados em $DATA_DIR)..."
  (isolado "$BIN/xerj" --data-dir "$DATA_DIR" > "$DATA_DIR/xerj.log" 2>&1 &)
  for _ in $(seq 1 30); do
    [ "$(curl -s -o /dev/null -w '%{http_code}' "$XERJ_URL" || true)" != "000" ] && [ -s "$DATA_DIR/admin.key" ] && break
    sleep 1
  done
fi

[ -s "$DATA_DIR/admin.key" ] || { echo "admin.key não encontrado em $DATA_DIR; veja $DATA_DIR/xerj.log" >&2; exit 1; }

for pasta in "$@"; do
  echo "Indexando $pasta..."
  isolado "XERJ_URL=$XERJ_URL" "XERJ_API_KEY=$(cat "$DATA_DIR/admin.key")" "$BIN/xerj" autoindex "$(cd "$pasta" && pwd)"
done
echo "xerj pronto em $XERJ_URL."

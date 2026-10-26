#!/usr/bin/env bash
# Confere se o GetYourBrain continua autocontido. Rode depois de atualizar vendor/.
set -uo pipefail
source "$(dirname "$0")/comum.sh"
exigir_binarios
falhas=0
ok()   { echo "  ok    $1"; }
erro() { echo "  FALHA $1"; falhas=$((falhas + 1)); }

echo "1. Cortes no código (cada arquivo precisa da marca GetYourBrain)"
while read -r arq; do
  [ -z "$arq" ] && continue
  if grep -q "GetYourBrain" "$RAIZ/vendor/$arq" 2>/dev/null; then ok "$arq"; else erro "$arq sem o corte"; fi
done <<'LISTA'
xerj/engine/crates/xerj-ai/src/neural.rs
xerj/engine/crates/xerj-ai/src/embed.rs
xerj/engine/crates/xerj-ai/Cargo.toml
xerj/engine/crates/xerj-rerank/src/lib.rs
xerj/engine/crates/xerj-engine/src/wal_tap.rs
xerj/engine/crates/xerj-hub/src/catalogue.rs
xerj/engine/crates/xerj-hub/src/cli.rs
xerj/engine/crates/xerj-hub/src/feedback.rs
xerj/engine/crates/xerj-autoindex/src/feedback.rs
xerj/engine/crates/xerj-autoindex/src/harvest/httpget.rs
xerj/engine/crates/xerj-autoindex/src/objsource.rs
xerj/engine/crates/xerj-autoindex/src/objwatch/s3.rs
xerj/engine/crates/xerj-autoindex/src/xc.rs
xerj/engine/crates/xerj-storage/src/s3.rs
xerj/engine/crates/xerj-server/src/share.rs
xerj/engine/crates/xerj-common/src/feedback.rs
xerj/engine/crates/xerj-common/src/corpus_feedback.rs
xerj/engine/crates/xerj-mcp/src/lib.rs
cortexdb/pkg/localonly/localonly.go
cortexdb/cmd/cortexdb-mcp-stdio/localonly.go
cortexdb/pkg/rpc/conn.go
cortexdb/pkg/cortexdb/cortexdb.go
cortexdb/pkg/liveview/assets.go
cortexdb/cmd/cortexdb-mcp-stdio/graph.go
LISTA

echo "2. Nenhuma página carrega script ou fonte de CDN"
cdn=$(grep -rlE '(src|href)="https?://(unpkg|cdn|fonts\.)|"https://unpkg\.com' \
  "$RAIZ/vendor/xerj/xerj-ux" "$RAIZ/vendor/cortexdb/cmd" "$RAIZ/vendor/cortexdb/pkg/liveview" 2>/dev/null | grep -v '_test\.go' || true)
[ -z "$cdn" ] && ok "sem CDN" || erro "CDN em: $cdn"

echo "3. Ferramentas que o MCP do xerj expõe"
lista=$(printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"verificacao","version":"1"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | isolado "XERJ_URL=$XERJ_URL" "$BIN/xerj" mcp 2>/dev/null | grep -o '"name":"xerj_[a-z_]*"' | sort -u)
[ -n "$lista" ] && ok "$(echo "$lista" | wc -l | tr -d ' ') ferramentas listadas" || erro "tools/list vazio"
proibidas=$(echo "$lista" | grep -E 'field_report|corpus_feedback|xerj_hub_' || true)
[ -z "$proibidas" ] && ok "nenhuma ferramenta que envia dados para fora" || erro "ainda expostas: $proibidas"

echo "4. Trava de loopback do CortexDB"
if (cd "$RAIZ/vendor/cortexdb" && go test ./pkg/localonly/ >/dev/null 2>&1); then ok "go test ./pkg/localonly"; else erro "go test ./pkg/localonly"; fi

echo "5. Sandbox de rede"
if [ "$(uname)" = "Darwin" ]; then
  if (isolado /usr/bin/curl -s -m 5 -o /dev/null https://example.com); then erro "o sandbox deixou sair para example.com"; else ok "saída externa bloqueada"; fi
else
  echo "  aviso sandbox indisponível fora do macOS"
fi

echo
[ "$falhas" -eq 0 ] && echo "Isolamento verificado." || { echo "$falhas falha(s)."; exit 1; }

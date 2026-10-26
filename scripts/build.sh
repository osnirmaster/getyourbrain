#!/usr/bin/env bash
# Compila xerj e CortexDB a partir do código em vendor/ e coloca os binários em bin/.
# Precisa de Rust (cargo) e Go. As dependências vêm do crates.io e do proxy do Go,
# travadas por vendor/xerj/engine/Cargo.lock e vendor/cortexdb/go.sum (conferidas por hash).
set -euo pipefail
source "$(dirname "$0")/comum.sh"
mkdir -p "$BIN"

echo "== xerj (Rust; a primeira vez leva alguns minutos)"
cargo build --release --locked --bin xerj --manifest-path "$RAIZ/vendor/xerj/engine/Cargo.toml"
install -m 755 "$RAIZ/vendor/xerj/engine/target/release/xerj" "$BIN/xerj"

echo "== cortexdb-mcp (Go)"
(cd "$RAIZ/vendor/cortexdb" && go build -trimpath -o "$BIN/cortexdb-mcp" ./cmd/cortexdb-mcp-stdio)

echo "== verificando"
"$RAIZ/scripts/verificar_isolamento.sh"

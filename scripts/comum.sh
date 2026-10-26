# Funções compartilhadas pelos scripts do GetYourBrain. Use com: source scripts/comum.sh
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$RAIZ/bin"
DADOS="$RAIZ/dados"
XERJ_URL="http://127.0.0.1:9200"

# Perfil do sandbox do macOS: nenhuma conexão de saída, exceto para a própria máquina.
# É a segunda camada; a primeira são os cortes no código em vendor/ (veja vendor/README.md).
PERFIL_SANDBOX='(version 1)(allow default)(deny network-outbound)(allow network-outbound (remote ip "localhost:*"))(allow network-outbound (remote unix-socket))'

# Roda um comando sem rede externa e com ambiente limpo: chaves de API e
# variáveis de proxy do seu shell (OPENAI_API_KEY, HF_ENDPOINT…) não chegam ao processo.
# Uso: isolado [VAR=valor ...] comando [args ...]
isolado() {
  exec_env=(env -i "HOME=$HOME" "PATH=/usr/bin:/bin" "TMPDIR=${TMPDIR:-/tmp}" "XERJ_DISABLE_FEEDBACK=true")
  while [[ "${1:-}" == *=* ]]; do exec_env+=("$1"); shift; done
  if [ "$(uname)" = "Darwin" ]; then
    "${exec_env[@]}" /usr/bin/sandbox-exec -p "$PERFIL_SANDBOX" "$@"
  else
    echo "aviso: sandbox de rede só existe no macOS; rodando apenas com os cortes do código" >&2
    "${exec_env[@]}" "$@"
  fi
}

exigir_binarios() {
  for b in xerj cortexdb-mcp; do
    [ -x "$BIN/$b" ] || { echo "$BIN/$b não existe; rode scripts/build.sh" >&2; exit 1; }
  done
}

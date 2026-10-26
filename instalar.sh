#!/usr/bin/env bash
# Instalador do GetYourBrain: confere os pré-requisitos, compila xerj e CortexDB,
# verifica o isolamento, sobe o xerj e, se você passar pastas, já indexa.
# Uso: ./instalar.sh [--recompilar] [pasta ...]
#   ./instalar.sh                                  # só instala e sobe o xerj
#   ./instalar.sh ~/repos/servico-pix ~/docs/pix   # instala e indexa as pastas
#   ./instalar.sh --recompilar                     # recompila mesmo com bin/ pronto
set -euo pipefail
source "$(dirname "$0")/scripts/comum.sh"

GO_MINIMO="1.25.0"
recompilar=0
pastas=()
for arg in "$@"; do
  case "$arg" in
    --recompilar) recompilar=1 ;;
    -h|--help) sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) [ -d "$arg" ] || { echo "pasta não encontrada: $arg" >&2; exit 1; }; pastas+=("$arg") ;;
  esac
done

etapa() { echo; echo "== $1"; }
falta=0
exigir() { # exigir <comando> <como instalar>
  if command -v "$1" >/dev/null 2>&1; then echo "  ok    $1"; else echo "  FALTA $1 ($2)"; falta=1; fi
}

etapa "1/5 Pré-requisitos"
if [ "$(uname)" = "Darwin" ]; then
  echo "  ok    macOS (sandbox de rede disponível)"
else
  echo "  aviso fora do macOS não há sandbox de rede; valem só os cortes no código"
fi
exigir curl "vem com o sistema"
if [ "$recompilar" -eq 1 ] || [ ! -x "$BIN/xerj" ] || [ ! -x "$BIN/cortexdb-mcp" ]; then
  precisa_compilar=1
  exigir cargo "https://rustup.rs"
  exigir go "https://go.dev/dl ou: brew install go"
else
  precisa_compilar=0
fi
# A verificação de isolamento roda go test, então o Go é necessário mesmo sem compilar.
[ "$precisa_compilar" -eq 0 ] && exigir go "https://go.dev/dl ou: brew install go"
if command -v go >/dev/null 2>&1; then
  go_atual="$(go env GOVERSION | sed 's/^go//')"
  if [ "$(printf '%s\n%s\n' "$GO_MINIMO" "$go_atual" | sort -V | head -1)" != "$GO_MINIMO" ]; then
    echo "  FALTA Go >= $GO_MINIMO (instalado: $go_atual)"; falta=1
  fi
fi
if command -v claude >/dev/null 2>&1; then
  echo "  ok    claude"
else
  echo "  aviso claude não encontrado; instale o Claude Code para usar o GetYourBrain"
fi
[ "$falta" -eq 0 ] || { echo; echo "Instale o que falta e rode ./instalar.sh de novo." >&2; exit 1; }

etapa "2/5 Compilação"
if [ "$precisa_compilar" -eq 1 ]; then
  "$RAIZ/scripts/build.sh"   # já termina com scripts/verificar_isolamento.sh
  verificado=1
else
  echo "  bin/xerj e bin/cortexdb-mcp já existem (use --recompilar para refazer)"
  verificado=0
fi

etapa "3/5 Isolamento"
if [ "$verificado" -eq 1 ]; then
  echo "  já verificado pelo build"
else
  "$RAIZ/scripts/verificar_isolamento.sh"
fi

etapa "4/5 Pastas de trabalho"
mkdir -p "$DADOS" "$RAIZ/saida"
echo "  ok    dados/ e saida/"
if [ ! -f "$RAIZ/temas.txt" ]; then
  cp "$RAIZ/temas.exemplo.txt" "$RAIZ/temas.txt"
  echo "  ok    temas.txt criado a partir de temas.exemplo.txt (edite com os seus temas)"
else
  echo "  ok    temas.txt já existe"
fi

etapa "5/5 xerj"
"$RAIZ/scripts/subir_xerj.sh" ${pastas[@]+"${pastas[@]}"}

cat <<FIM

GetYourBrain instalado.

Próximos passos (abra o Claude Code na raiz do projeto: cd "$RAIZ" && claude):
FIM
[ "${#pastas[@]}" -eq 0 ] && echo "  /indexar <pasta> [pasta ...]       indexa repositórios ou documentação"
cat <<'FIM'
  /curar --arquivo temas.txt         cataloga as regras no grafo
  /perguntar <sua pergunta>          responde com fonte (arquivo:linha)

Na primeira vez, o Claude Code pede para aprovar os servidores MCP do .mcp.json (xerj e cortexdb).
FIM

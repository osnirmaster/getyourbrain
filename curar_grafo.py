"""Popula o grafo de regras de negócio no CortexDB a partir do que o xerj indexou.

Uso:
    python curar_grafo.py "limites do PIX" "tarifas de TED"
    python curar_grafo.py --arquivo temas.txt   # um tema por linha; linhas com # são ignoradas
"""

import argparse
from pathlib import Path

from agentes import criar_curador
from config import carregar, criar_modelo
from servidores_mcp import cliente_cortex, cliente_xerj


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("temas", nargs="*", help="temas de negócio a catalogar")
    parser.add_argument("--arquivo", type=Path, help="arquivo com um tema por linha")
    args = parser.parse_args()

    temas = list(args.temas)
    if args.arquivo:
        linhas = args.arquivo.read_text(encoding="utf-8").splitlines()
        temas += [t.strip() for t in linhas if t.strip() and not t.lstrip().startswith("#")]
    if not temas:
        parser.error("informe ao menos um tema")

    cfg = carregar()
    modelo = criar_modelo(cfg)
    xerj, cortex = cliente_xerj(cfg), cliente_cortex(cfg)
    with xerj, cortex:
        ferramentas_xerj, ferramentas_cortex = xerj.list_tools_sync(), cortex.list_tools_sync()
        for i, tema in enumerate(temas, 1):
            print(f"\n=== [{i}/{len(temas)}] {tema} ===")
            # Um curador novo por tema, para o contexto não crescer entre temas.
            criar_curador(modelo, ferramentas_xerj, ferramentas_cortex)(
                f"Catalogue no grafo as regras de negócio e dependências do tema: {tema}"
            )


if __name__ == "__main__":
    main()

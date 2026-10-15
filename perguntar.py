"""Tira dúvidas sobre regras de negócio e gera diagramas.

Uso:
    python perguntar.py                                  # modo interativo
    python perguntar.py "Qual o limite do PIX noturno?"  # pergunta única
    python perguntar.py --ferramentas                    # lista as ferramentas MCP expostas
"""

import argparse
import re
from datetime import datetime

from agentes import criar_orquestrador
from config import carregar, criar_modelo
from servidores_mcp import cliente_cortex, cliente_xerj

BLOCO_MERMAID = re.compile(r"```mermaid\n.*?```", re.DOTALL)


def listar_ferramentas(cfg) -> None:
    for nome, cliente in (("xerj", cliente_xerj(cfg, filtrar=False)), ("cortexdb", cliente_cortex(cfg, filtrar=False))):
        with cliente:
            print(f"\n== {nome} ==")
            for f in cliente.list_tools_sync():
                print(f"- {f.mcp_tool.name}: {(f.mcp_tool.description or '').splitlines()[0][:100]}")


def salvar_diagramas(cfg, pergunta: str, resposta: str) -> None:
    if not BLOCO_MERMAID.search(resposta):
        return
    cfg.pasta_saida.mkdir(exist_ok=True)
    arquivo = cfg.pasta_saida / f"diagrama-{datetime.now():%Y%m%d-%H%M%S}.md"
    arquivo.write_text(f"# {pergunta}\n\n{resposta}\n", encoding="utf-8")
    print(f"\n[diagrama salvo em {arquivo}]")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pergunta", nargs="?", help="pergunta única; sem ela, abre o modo interativo")
    parser.add_argument("--ferramentas", action="store_true", help="lista as ferramentas dos servidores MCP e sai")
    args = parser.parse_args()

    cfg = carregar()
    if args.ferramentas:
        listar_ferramentas(cfg)
        return

    xerj, cortex = cliente_xerj(cfg), cliente_cortex(cfg)
    with xerj, cortex:
        orquestrador = criar_orquestrador(criar_modelo(cfg), xerj.list_tools_sync(), cortex.list_tools_sync())

        def responder(pergunta: str) -> None:
            resposta = str(orquestrador(pergunta))
            print()
            salvar_diagramas(cfg, pergunta, resposta)

        if args.pergunta:
            responder(args.pergunta)
            return

        print("Base de conhecimento pronta. Digite sua pergunta (ou 'sair').")
        while (pergunta := input("\n> ").strip()).lower() not in {"sair", "exit", "quit"}:
            if pergunta:
                responder(pergunta)


if __name__ == "__main__":
    main()

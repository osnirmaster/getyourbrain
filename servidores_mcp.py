"""Conexão com os servidores MCP do xerj (busca) e do CortexDB (grafo de conhecimento).

Cada servidor é iniciado como subprocesso via stdio. Só as ferramentas listadas
abaixo são carregadas, para manter o contexto do modelo enxuto e impedir que
agentes de consulta escrevam no grafo.
"""

import sys

from mcp import StdioServerParameters, stdio_client
from strands.tools.mcp import MCPClient

from config import Config

# xerj: só leitura. Memória e "second brain" do xerj ficam de fora porque esse
# papel é do CortexDB; o rerank externo (Jev) não é usado.
XERJ_BUSCA = [
    "xerj_map",
    "xerj_plan",
    "xerj_search",
    "xerj_hybrid_search",
    "xerj_semantic_search",
    "xerj_code_search",
]

# CortexDB: leitura para quem responde perguntas, escrita só para o curador.
CORTEX_LEITURA = ["knowledge_search", "knowledge_graph_query", "build_context"]
CORTEX_ESCRITA = ["knowledge_save", "knowledge_graph_upsert", "knowledge_graph_shacl_validate"]


def cliente_xerj(cfg: Config, filtrar: bool = True) -> MCPClient:
    env = {"XERJ_URL": cfg.xerj_url}
    if cfg.xerj_api_key:
        env["XERJ_AUTH"] = f"ApiKey {cfg.xerj_api_key}"
    params = StdioServerParameters(command=cfg.xerj_bin, args=["mcp"], env=env)
    return MCPClient(
        lambda: stdio_client(params),
        tool_filters={"allowed": XERJ_BUSCA} if filtrar else None,
        startup_timeout=60,
    )


def cliente_cortex(cfg: Config, filtrar: bool = True) -> MCPClient:
    params = StdioServerParameters(
        command=cfg.cortexdb_mcp_bin,
        env={"CORTEXDB_PATH": cfg.cortexdb_path},
    )
    return MCPClient(
        lambda: stdio_client(params),
        tool_filters={"allowed": CORTEX_LEITURA + CORTEX_ESCRITA} if filtrar else None,
        startup_timeout=60,
    )


def selecionar(ferramentas: list, nomes: list[str]) -> list:
    """Filtra as ferramentas carregadas pelo nome original no servidor MCP."""
    escolhidas = [f for f in ferramentas if f.mcp_tool.name in nomes]
    faltando = sorted(set(nomes) - {f.mcp_tool.name for f in escolhidas})
    if faltando:
        print(
            f"[aviso] ferramentas MCP não encontradas: {', '.join(faltando)}. "
            "Rode `python perguntar.py --ferramentas` para ver o que o servidor expõe "
            "e ajuste as listas em servidores_mcp.py.",
            file=sys.stderr,
        )
    return escolhidas

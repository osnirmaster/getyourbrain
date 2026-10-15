"""Configuração do GetYourBrain: lida do arquivo .env (veja .env.example)."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent
load_dotenv(RAIZ / ".env")


@dataclass(frozen=True)
class Config:
    provedor: str
    model_id: str
    aws_region: str
    bedrock_guardrail_id: str | None
    bedrock_guardrail_version: str | None
    anthropic_api_key: str | None
    ollama_host: str
    xerj_bin: str
    xerj_url: str
    xerj_api_key: str | None
    cortexdb_mcp_bin: str
    cortexdb_path: str
    pasta_saida: Path


def carregar() -> Config:
    provedor = os.getenv("PROVEDOR", "bedrock").lower()
    modelo_padrao = {
        "bedrock": "global.anthropic.claude-opus-5-5",
        "anthropic": "claude-opus-5-5",
        "ollama": "qwen3:32b",
    }
    if provedor not in modelo_padrao:
        raise SystemExit(f"PROVEDOR inválido: {provedor!r}. Use bedrock, anthropic ou ollama.")

    return Config(
        provedor=provedor,
        model_id=os.getenv("MODEL_ID") or modelo_padrao[provedor],
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        bedrock_guardrail_id=os.getenv("BEDROCK_GUARDRAIL_ID") or None,
        bedrock_guardrail_version=os.getenv("BEDROCK_GUARDRAIL_VERSION") or None,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        xerj_bin=os.path.expanduser(os.getenv("XERJ_BIN", "~/.local/bin/xerj")),
        xerj_url=os.getenv("XERJ_URL", "http://localhost:9200"),
        xerj_api_key=_ler_chave_xerj(),
        cortexdb_mcp_bin=os.path.expanduser(os.getenv("CORTEXDB_MCP_BIN", "~/.local/bin/cortexdb-mcp")),
        cortexdb_path=str(_caminho(os.getenv("CORTEXDB_PATH", "dados/cortexdb.db"), criar_pai=True)),
        pasta_saida=RAIZ / "saida",
    )


def _caminho(valor: str, criar_pai: bool = False) -> Path:
    """Expande ~ e resolve caminhos relativos a partir da pasta do projeto."""
    caminho = Path(os.path.expanduser(valor))
    caminho = caminho if caminho.is_absolute() else RAIZ / caminho
    if criar_pai:
        caminho.parent.mkdir(parents=True, exist_ok=True)
    return caminho


def _ler_chave_xerj() -> str | None:
    """A chave vem de XERJ_API_KEY ou do admin.key que o xerj gera no primeiro boot."""
    if chave := os.getenv("XERJ_API_KEY"):
        return chave
    arquivo = _caminho(os.getenv("XERJ_DATA_DIR", "dados/xerj")) / "admin.key"
    return arquivo.read_text().strip() if arquivo.exists() else None


def criar_modelo(cfg: Config):
    """Instancia o modelo do Strands conforme o provedor escolhido."""
    if cfg.provedor == "bedrock":
        from strands.models import BedrockModel

        extras = {}
        if cfg.bedrock_guardrail_id:
            extras = {
                "guardrail_id": cfg.bedrock_guardrail_id,
                "guardrail_version": cfg.bedrock_guardrail_version or "DRAFT",
            }
        return BedrockModel(model_id=cfg.model_id, region_name=cfg.aws_region, max_tokens=16000, **extras)

    if cfg.provedor == "anthropic":
        from strands.models.anthropic import AnthropicModel

        client_args = {"api_key": cfg.anthropic_api_key} if cfg.anthropic_api_key else {}
        return AnthropicModel(client_args=client_args, model_id=cfg.model_id, max_tokens=16000)

    from strands.models.ollama import OllamaModel

    return OllamaModel(cfg.ollama_host, model_id=cfg.model_id)

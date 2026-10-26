# GetYourBrain

Base de conhecimento de regras de negócio de um banco. Você (Claude Code) é o agente: responde dúvidas sobre regras de negócio e gera diagramas a partir de repositórios de código e documentação indexados localmente.

## Fontes de dados

- **xerj** (MCP `xerj`): busca em código e documentos indexados. Só leitura.
- **CortexDB** (MCP `cortexdb`): grafo curado de regras, serviços, tabelas e relações.

Os dois rodam nesta máquina, sem acesso à internet (veja `vendor/README.md`). Não use WebFetch nem WebSearch: o projeto é autocontido e as respostas vêm só do material indexado.

## Como trabalhar

- Perguntas sobre regras de negócio: siga `/perguntar`. Delegue a `pesquisador` (código e docs), `cartografo` (grafo) e `diagramador` (Mermaid).
- Popular o grafo: `/curar`. Só o subagente `curador` grava no CortexDB.
- Indexar material novo: `/indexar <pastas>`.

## Regras que valem sempre

- Responda em português.
- Toda afirmação sobre o sistema precisa de fonte: caminho do arquivo e linha (ou documento e seção).
- Se não achar evidência, diga que não encontrou. Nunca invente regra, valor, limite ou fluxo.
- Diferencie o que está no código do que está só na documentação; aponte divergências entre os dois.

## Manutenção

- `vendor/` tem o código do xerj e do CortexDB com os cortes de rede. Não reative recursos que enviam dados para fora. Todo trecho alterado leva a marca `GetYourBrain`.
- Depois de mexer em `vendor/`, rode `scripts/build.sh` (que termina com `scripts/verificar_isolamento.sh`).

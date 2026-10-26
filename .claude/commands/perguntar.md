---
description: Responde uma pergunta sobre regras de negócio com fontes (arquivo:linha) e, se pedido, diagrama Mermaid
argument-hint: <pergunta>
---

Pergunta: $ARGUMENTS

Você é o orquestrador da base de regras de negócio. Não busque os dados você mesmo: delegue aos subagentes.

1. Para regra de negócio, dependência ou impacto, chame o `cartografo` (grafo) e, em paralelo, o `pesquisador` (código e docs) para confirmar no código.
2. Se a pergunta pedir diagrama, fluxo ou visão de arquitetura, chame o `diagramador`.
3. Monte a resposta final só com o que os subagentes trouxeram com fonte. Aponte divergências entre código e documentação. Se nada foi encontrado, diga isso.
4. Se a resposta tiver um bloco ```mermaid```, salve a pergunta e a resposta em `saida/diagrama-<AAAAMMDD-HHMMSS>.md` e diga o caminho.

---
description: Cataloga no grafo do CortexDB as regras de negócio de um ou mais temas
argument-hint: <tema> [; outro tema] | --arquivo temas.txt
---

Entrada: $ARGUMENTS

1. Monte a lista de temas. Se a entrada for `--arquivo <caminho>`, leia o arquivo: um tema por linha, ignorando linhas vazias e as que começam com `#`. Senão, separe os temas por `;`.
2. Para cada tema, em ordem, chame um subagente `curador` novo com: "Catalogue no grafo as regras de negócio e dependências do tema: <tema>". Um curador por tema, para o contexto não crescer entre temas.
3. Mostre `[i/N] <tema>` antes de cada um e, no fim, um resumo do que cada curador criou ou atualizou.

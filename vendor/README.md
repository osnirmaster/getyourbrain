# vendor/

Código-fonte do xerj e do CortexDB, trazido para dentro do GetYourBrain e alterado para que **nenhum dado saia da máquina**. `scripts/build.sh` compila os dois em `bin/`.

| Projeto | Versão | Commit | Licença |
|---|---|---|---|
| [xerj](https://github.com/xerj-org/xerj) | v1.0.0-rc.99 | `e3c14a28dfb9fd677f650e310630db51cea431b0` | Apache-2.0 (`xerj/LICENSE`, `xerj/NOTICE`) |
| [CortexDB](https://github.com/liliang-cn/cortexdb) | v2.139.0 | `7acac1abd6c99d874c42d36e663af6e8a0732c52` | MIT (`cortexdb/LICENSE`) |

O diff exato contra o upstream está em `patches/xerj.patch` e `patches/cortexdb.patch`. Todo trecho alterado leva a marca `GetYourBrain`, e `scripts/verificar_isolamento.sh` confere se cada corte continua lá.

## O que foi cortado no xerj

O próprio xerj mantém um inventário de conexões de saída (`xerj-rerank/tests/egress_inventory.rs` no upstream). Cada item dele foi desligado na origem: a função que abriria a conexão agora devolve erro.

| Recurso | O que enviava | Onde foi cortado |
|---|---|---|
| Rerank externo (Jev/TypeSafe) | texto dos documentos e a pergunta para `api.typesafe.ai` | `xerj-rerank/src/lib.rs` |
| Embeddings por proxy | texto dos documentos e das buscas para uma API de embeddings | `xerj-ai/src/embed.rs` |
| WAL tap | cada escrita para um `_bulk` externo | `xerj-engine/src/wal_tap.rs` |
| Download de modelo neural | busca o modelo no HuggingFace (dependência `hf-hub` removida) | `xerj-ai/src/neural.rs`, `xerj-ai/Cargo.toml` |
| Corpus Hub | baixa catálogo e pacotes de `hub.xerj.org` | `xerj-hub/src/catalogue.rs`, `xerj-hub/src/cli.rs` |
| Avaliação de corpus | envia avaliação automática para `hub.xerj.org` | `xerj-hub/src/feedback.rs` |
| Field report | abre PR no GitHub ou faz POST em `xerj.org`, "sem perguntar ao usuário" | `xerj-autoindex/src/feedback.rs`, `xerj-common/src/feedback.rs` |
| Ferramentas MCP `xerj_field_report`, `xerj_corpus_feedback`, `xerj_hub_*` | os itens acima, via agente | removidas de `tools/list` e das instruções em `xerj-mcp/src/lib.rs` |
| `xerj share --tunnel` | abre endereço público via `cloudflared` | `xerj-server/src/share.rs` |
| `xerj corpus build` | baixa zips e faz `git clone` da internet | `xerj-autoindex/src/harvest/httpget.rs`, `xerj-autoindex/src/xc.rs` |
| Armazenamento e fontes S3/R2 | grava o índice ou lê objetos de um bucket | `xerj-storage/src/s3.rs`, `xerj-autoindex/src/objsource.rs`, `xerj-autoindex/src/objwatch/s3.rs` |
| Google Fonts no console | o navegador buscava fontes no Google | `xerj-ux/*.html` |

Ficou o modo cluster (Raft), que só conversa com peers configurados explicitamente. O GetYourBrain roda um nó único em `127.0.0.1`.

Sem download de modelo, o xerj usa o embedder léxico padrão. Para usar o neural, coloque `config.json`, `tokenizer.json` e `model.safetensors` numa pasta e aponte `embedding.local_model_dir` para ela.

Também foram removidos do código trazido: site, benchmarks, demos, relatos de usuários, docs e scripts de release, que não entram no binário.

## O que foi cortado no CortexDB

Toda saída do CortexDB dependia de variável de ambiente: embedder (inclusive `OPENAI_API_KEY`/`OPENAI_BASE_URL` como fallback), LLM, reranker, cérebro remoto via gRPC e PostgreSQL. Em vez de mexer em cada cliente, há uma trava única:

- `pkg/localonly`: troca o `http.DefaultTransport` por um que só conecta em loopback (nomes que não sejam `localhost` são recusados antes do DNS). Ativado no `init()` do binário (`cmd/cortexdb-mcp-stdio/localonly.go`). Testado em `pkg/localonly/localonly_test.go`.
- `pkg/rpc/conn.go`: o gRPC usa o mesmo discador de loopback.
- `pkg/cortexdb/cortexdb.go`: só aceita arquivo SQLite local, nada de `postgres://`.
- `render_graph_html` e a página "library" do liveview carregavam vis-network e three.js do unpkg. Agora vão embutidos no binário (vis-network 9.1.9 e three 0.168.0, conferidos pelo hash `integrity` do npm).

Também foram removidos os exemplos e os binários que o GetYourBrain não usa (`cortexdb-bench`, que baixava datasets, `cortexdb-grpc` e `cortexdb-connector-mcp`).

## Segunda camada: sandbox

Mesmo com os cortes, `scripts/comum.sh` roda o xerj e o CortexDB com ambiente limpo (`env -i`, sem as chaves do seu shell) e, no macOS, dentro do `sandbox-exec` com a saída de rede negada, exceto para o localhost.

## Atualizar uma versão

1. Clone a tag nova do upstream numa pasta temporária.
2. Reaplique os patches: `git apply vendor/patches/<projeto>.patch` e resolva os conflitos.
3. Confira se o inventário de saída do xerj (`egress_inventory.rs`) ganhou itens novos e corte-os também.
4. Rode `scripts/build.sh`. Ele termina com `scripts/verificar_isolamento.sh`.

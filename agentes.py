"""Agentes do GetYourBrain.

- pesquisador: encontra trechos de código e documentação no xerj (com arquivo:linha).
- cartografo: consulta o grafo de regras de negócio no CortexDB (só leitura).
- diagramador: transforma fatos do grafo + trechos do código em diagramas Mermaid.
- curador: lê o código via xerj e grava regras/relações no grafo do CortexDB.
- orquestrador: recebe a pergunta do usuário e delega aos três primeiros.
"""

from strands import Agent, tool

from servidores_mcp import CORTEX_ESCRITA, CORTEX_LEITURA, XERJ_BUSCA, selecionar

REGRAS_GERAIS = """
Regras que valem sempre:
- Responda em português.
- Toda afirmação sobre o sistema precisa de fonte: caminho do arquivo e linha (ou documento e seção).
- Se não achar evidência, diga que não encontrou. Nunca invente regra, valor, limite ou fluxo.
- Diferencie o que está no código do que está só na documentação; aponte divergências entre os dois.
"""

ONTOLOGIA = """
Vocabulário do grafo (use exatamente estes tipos e relações):
Tipos: RegraDeNegocio, Servico, Componente (classe/módulo), Endpoint, Tabela, Evento, Documento, Dominio.
Relações:
- RegraDeNegocio implementadaEm Componente
- RegraDeNegocio documentadaEm Documento
- RegraDeNegocio pertenceA Dominio
- Componente parteDe Servico
- Servico chama Servico / Servico expoe Endpoint
- Componente le Tabela / Componente escreve Tabela
- Servico publica Evento / Servico consome Evento
Toda entidade e relação leva a propriedade `fonte` (arquivo:linha ou documento#seção).
"""

PROMPT_PESQUISADOR = f"""Você é o pesquisador da base de conhecimento de um banco.
Use as ferramentas do xerj para localizar código e documentação.
Comece com xerj_map para descobrir os índices disponíveis; prefira xerj_hybrid_search
para perguntas em linguagem natural e xerj_code_search para símbolos e implementações.
Devolva os trechos relevantes resumidos, sempre com arquivo:linha.
{REGRAS_GERAIS}"""

PROMPT_CARTOGRAFO = f"""Você consulta o grafo de conhecimento de regras de negócio no CortexDB.
Use as ferramentas de busca e consulta ao grafo para responder sobre regras, dependências
entre serviços e impacto de mudanças. Devolva os fatos encontrados com suas fontes.
{ONTOLOGIA}
{REGRAS_GERAIS}"""

PROMPT_DIAGRAMADOR = f"""Você gera diagramas Mermaid a partir de fatos verificados.
1. Consulte o grafo no CortexDB para obter entidades e relações do tema pedido.
2. Complete lacunas com buscas no xerj (código e docs).
3. Escolha o tipo certo: sequenceDiagram para fluxos entre serviços, flowchart para regras
   e decisões, erDiagram para tabelas, classDiagram para componentes.
4. Entregue um bloco ```mermaid``` e, abaixo dele, a lista de fontes de cada elemento.
Não desenhe nada que não tenha fonte.
{ONTOLOGIA}
{REGRAS_GERAIS}"""

PROMPT_CURADOR = f"""Você é o curador do grafo de conhecimento de regras de negócio.
Para o tema recebido:
1. Use o xerj para encontrar onde o tema é implementado e documentado.
2. Leia os trechos e extraia regras de negócio, componentes, serviços, tabelas, eventos e relações.
3. Antes de gravar, consulte o grafo para não duplicar entidades já existentes.
4. Grave as entidades e relações no CortexDB com knowledge_graph_upsert, no formato que a
   ferramenta pede, e um resumo textual de cada regra com knowledge_save.
5. Se a validação SHACL estiver disponível, rode-a no fim.
Ao terminar, liste o que foi criado ou atualizado, com as fontes.
{ONTOLOGIA}
{REGRAS_GERAIS}"""

PROMPT_ORQUESTRADOR = f"""Você é o assistente de regras de negócio de um banco, para desenvolvedores e analistas.
Você não acessa os dados diretamente; delega a especialistas:
- consultar_codigo_e_docs: busca em código e documentação.
- consultar_grafo: regras catalogadas, dependências e análise de impacto.
- gerar_diagrama: quando o usuário pedir diagrama, fluxo ou visão de arquitetura.
Para perguntas sobre regra de negócio, consulte o grafo e confirme no código.
Monte a resposta final com as fontes que os especialistas devolverem.
{REGRAS_GERAIS}"""


def criar_orquestrador(modelo, ferramentas_xerj: list, ferramentas_cortex: list) -> Agent:
    busca = selecionar(ferramentas_xerj, XERJ_BUSCA)
    grafo_leitura = selecionar(ferramentas_cortex, CORTEX_LEITURA)

    def especialista(prompt: str, ferramentas: list, nome: str) -> Agent:
        # Um agente novo por chamada: sem histórico acumulado entre perguntas.
        return Agent(model=modelo, system_prompt=prompt, tools=ferramentas, name=nome, callback_handler=None)

    @tool
    def consultar_codigo_e_docs(pergunta: str) -> str:
        """Busca trechos de código e documentação relacionados à pergunta, com arquivo:linha.

        Args:
            pergunta: O que procurar, em linguagem natural ou nome de símbolo.
        """
        return str(especialista(PROMPT_PESQUISADOR, busca, "pesquisador")(pergunta))

    @tool
    def consultar_grafo(pergunta: str) -> str:
        """Consulta o grafo de regras de negócio: regras, dependências e impacto de mudanças.

        Args:
            pergunta: A pergunta sobre regras, serviços ou relações.
        """
        return str(especialista(PROMPT_CARTOGRAFO, grafo_leitura, "cartografo")(pergunta))

    @tool
    def gerar_diagrama(pedido: str) -> str:
        """Gera um diagrama Mermaid com fontes para o tema ou fluxo pedido.

        Args:
            pedido: O que o diagrama deve mostrar (ex.: fluxo de aprovação de crédito).
        """
        return str(especialista(PROMPT_DIAGRAMADOR, busca + grafo_leitura, "diagramador")(pedido))

    return Agent(
        model=modelo,
        system_prompt=PROMPT_ORQUESTRADOR,
        tools=[consultar_codigo_e_docs, consultar_grafo, gerar_diagrama],
        name="orquestrador",
    )


def criar_curador(modelo, ferramentas_xerj: list, ferramentas_cortex: list) -> Agent:
    ferramentas = selecionar(ferramentas_xerj, XERJ_BUSCA) + selecionar(
        ferramentas_cortex, CORTEX_LEITURA + CORTEX_ESCRITA
    )
    return Agent(model=modelo, system_prompt=PROMPT_CURADOR, tools=ferramentas, name="curador")

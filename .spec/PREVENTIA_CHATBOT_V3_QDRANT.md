# SPEC — PreventIA com Análise de CSV, RAG no Qdrant e Catálogo de Coleções

**Status:** proposta para construção  
**Versão:** 3.0  
**Data:** 2026-10-20  
**Produto:** PreventIA — motor de prevenção de perdas usando IA  
**Baseline:** `.spec/PREVENTIA_CHATBOT_V2.md`  
**Interface inicial:** aplicação web em Streamlit  
**Idioma inicial:** português do Brasil (pt-BR)

## 1. Objetivo

Evoluir o PreventIA para que o usuário autorizado possa:

1. enviar arquivos `.csv` com dados de prevenção de perdas;
2. validar, perfilar e analisar os dados com uma engine determinística;
3. fazer perguntas em linguagem natural e receber explicações da IA;
4. consultar bases documentais por RAG usando o Qdrant;
5. visualizar, no próprio chat, as coleções Qdrant que estão disponíveis para seu escopo;
6. combinar resultados de CSV e documentos, separando cálculo, evidência e hipótese.

Esta versão torna o Qdrant e o modelo de embeddings decisões arquiteturais obrigatórias. A UI não acessa o Qdrant diretamente: toda descoberta de coleções, consulta e mutação passa por serviços autenticados e autorizados.

## 2. Princípios e decisões de alto nível

- **A IA interpreta; a engine tabular calcula.** Totais, médias, percentuais, filtros e agrupamentos não podem depender de aritmética feita pelo LLM.
- **RAG com evidência.** Toda afirmação derivada de documento deve apontar para fonte, versão, seção/página e chunk utilizado.
- **Qdrant como índice vetorial oficial.** O Qdrant armazena pontos vetoriais e payloads de recuperação; o catálogo, permissões, ciclo de vida e auditoria ficam no PostgreSQL.
- **Embeddings padronizados.** O contrato inicial usa `embedding_model_name="BAAI/bge-m3"`, vetores densos de 1024 dimensões, normalizados e distância `Cosine`.
- **Coleção técnica não é permissão.** O nome da coleção Qdrant nunca será usado como mecanismo de autorização. O acesso será resolvido por catálogo, tenant, domínio, unidade, região, classificação e vigência.
- **Conteúdo recuperado é dado não confiável.** Documentos, CSVs, metadados e chunks podem conter prompt injection e não podem alterar as instruções do sistema.
- **Falha segura.** Se não houver evidência suficiente ou a coleção não estiver autorizada, o sistema informa a limitação; não faz fallback silencioso para outra coleção.
- **Nenhuma ação operacional automática.** A primeira entrega somente analisa e recomenda; não altera estoque, preço, pedido, cadastro ou sistema de loja.

## 3. Escopo

### Incluído

- Upload autenticado de CSV, quarentena, validação, perfilamento e versionamento.
- Engine tabular segura com plano declarativo allowlisted.
- Conversa com intenção de análise CSV, consulta RAG, consulta híbrida ou conversa geral.
- Pipeline de ingestão documental assíncrono.
- Qdrant para busca vetorial, filtros por payload e recuperação de chunks.
- Embeddings locais ou hospedados sob adapter, com `BAAI/bge-m3` como modelo inicial obrigatório.
- Catálogo de coleções e fontes no PostgreSQL.
- Listagem de coleções autorizadas no próprio chat e, opcionalmente, em uma área de configuração.
- Busca semântica, filtro por metadados, citações, versionamento e despublicação.
- Observabilidade, auditoria, avaliação de retrieval e testes de isolamento entre escopos.

### Fora do escopo da primeira entrega

- Fine-tuning ou treinamento do BGE-M3 ou do LLM.
- Indexação automática de cada linha do CSV como vetor.
- Execução de Python, SQL, shell ou código produzido pelo usuário/LLM.
- Escrita em sistemas de operação de loja, ERP, estoque ou preços.
- Exposição da API, URL, chave ou painel administrativo do Qdrant no chat.
- Coleções públicas sem ACL explícita.
- Decisão autônoma de fraude, acusação ou medida disciplinar.
- Migração automática de todas as coleções antigas sem validação de compatibilidade do embedding.

## 4. Capacidade de negócio e perfis

### Capacidade habilitada

**Investigação assistida de perdas com conhecimento corporativo contextual.** O analista consegue partir de dados operacionais, localizar procedimentos aplicáveis e produzir hipóteses auditáveis em uma única conversa.

### Perfis

| Perfil | Uso principal | Permissões mínimas |
|---|---|---|
| Operador de loja | Envia CSV e consulta indicadores básicos | Datasets próprios/compartilhados e coleções da sua unidade |
| Analista de prevenção | Investiga padrões e consulta políticas | Datasets autorizados e coleções de seu domínio/região |
| Gestor | Consulta sínteses e evidências | Leitura dos escopos atribuídos |
| Curador de conhecimento | Publica, reindexa e despublica fontes | Gerenciar fontes e coleções autorizadas |
| Administrador técnico | Configura infraestrutura e políticas | Operar Qdrant sem acesso implícito ao conteúdo |

## 5. Requisitos funcionais

### RF-01 — Conversa e análise de CSV

- Permitir upload de `.csv` pelo chat e associar o dataset à conversa.
- Validar tamanho, conteúdo, encoding, delimitador, cabeçalho, estrutura, número de linhas e colunas.
- Gerar `dataset_id` opaco, versão imutável e status de processamento.
- Exibir perfilamento, ambiguidades e advertências antes da análise.
- Gerar e validar plano de análise; executar apenas funções, colunas e operadores permitidos.
- Exibir números calculados, parâmetros, dataset, versão, filtros e limitações.
- Nunca enviar o CSV inteiro ao LLM por padrão.

### RF-02 — Ingestão de conhecimento

- Permitir cadastro de fontes aprovadas, inicialmente PDF, Markdown, HTML e TXT.
- Exigir `title`, proprietário, domínio, versão, vigência, classificação e escopo de acesso.
- Manter original imutável e criar ingestões versionadas.
- Extrair texto preservando título, seção, página/posição e hash do conteúdo.
- Dividir o texto em chunks com estratégia versionada.
- Gerar o embedding de cada chunk com o modelo configurado e persistir o ponto somente após validação do vetor.
- Permitir reprocessamento, falha parcial por documento, retry e dead-letter.
- Permitir publicar, despublicar, expirar e excluir conforme retenção.

### RF-03 — Indexação no Qdrant

- Usar uma collection Qdrant compatível com o contrato do modelo: `size=1024` e `distance=Cosine`.
- Armazenar no ponto Qdrant um identificador estável e payload mínimo para filtragem e citação.
- Usar `document_id`, `document_version`, `chunk_id`, `tenant_id`, `domain`, `unit_ids`, `region_ids`, `classification`, `valid_from`, `valid_to`, `status` e `content_hash` como metadados filtráveis.
- O texto do chunk pode permanecer no object storage ou no PostgreSQL; o payload deve conter apenas o necessário para retrieval, citação e auditoria.
- Garantir idempotência por `collection_id + chunk_id + embedding_model_version`.
- Validar a dimensão e a finitude de todos os vetores antes do upsert.
- Não misturar embeddings de modelos, dimensões ou normalização incompatíveis na mesma collection.
- Usar aliases ou estratégia equivalente para troca controlada de coleção durante reindexação.

### RF-04 — Consulta RAG

- Classificar a intenção e resolver as coleções autorizadas antes de gerar a consulta vetorial.
- Converter a pergunta em embedding com o mesmo `BAAI/bge-m3` usado na coleção consultada.
- Aplicar filtro de ACL e vigência no próprio `search/query` do Qdrant, antes da composição do contexto.
- Recuperar `top_k` limitado e, se habilitado, aplicar reranking em serviço separado.
- Buscar o texto completo dos chunks selecionados pelo identificador controlado, sem confiar em conteúdo arbitrário do payload.
- Enviar ao LLM somente chunks autorizados e identificados para citação.
- Retornar “não encontrei evidência suficiente” quando o score mínimo ou a cobertura de evidência não forem atingidos.
- Não permitir que o conteúdo do documento altere ferramentas, persona, permissões ou políticas de segurança.

### RF-05 — Listagem de coleções no próprio chat

O chat deve ter uma capacidade explícita de descoberta controlada:

- Ao iniciar a conversa, o sistema pode exibir um cartão discreto **“Coleções de conhecimento disponíveis”**, sem carregar os documentos.
- O usuário pode perguntar em linguagem natural “quais coleções estão disponíveis?” ou acionar um botão **“Ver coleções disponíveis”**.
- O backend resolve a identidade e retorna somente collections com status publicado/ativo e autorização para aquele usuário.
- A resposta aparece como uma mensagem estruturada do assistente no histórico do chat, com tabela ou cartões contendo:
  - nome amigável e identificador lógico da base;
  - descrição e domínio;
  - escopo acessível, sem revelar escopos de terceiros;
  - quantidade aproximada de documentos/chunks, quando permitido;
  - status de atualização e data da última sincronização;
  - modelo de embedding e versão do índice;
  - ação **“Consultar esta coleção”**, que define o escopo da próxima pergunta.
- O nome técnico do Qdrant pode ser omitido por padrão e mostrado somente a perfis autorizados.
- Se não houver collections acessíveis, o chat deve informar isso sem revelar a existência de collections restritas.
- A listagem deve ser paginada e ter limite de quantidade para evitar enumeração indevida.
- Cada listagem deve gerar evento de auditoria sem registrar token ou conteúdo documental.

Exemplo de resposta no chat:

```text
Coleções de conhecimento disponíveis para seu perfil:

1. Políticas de Prevenção — Operações Brasil
   Atualização: 2026-10-18 | Documentos: 184 | Embedding: BAAI/bge-m3

2. Procedimentos de Inventário — Região Sudeste
   Atualização: 2026-10-15 | Documentos: 76 | Embedding: BAAI/bge-m3

Selecione uma coleção ou faça uma pergunta para iniciar a consulta.
```

Os números acima são apenas o formato da interface; a aplicação deve preenchê-los a partir do catálogo autorizado, nunca de dados fictícios.

### RF-06 — Consulta híbrida CSV + RAG

- Executar a análise tabular e a recuperação do Qdrant como etapas separadas.
- Não permitir que um documento modifique silenciosamente o plano ou os filtros do CSV.
- Compor a resposta em quatro blocos: **resultado calculado**, **evidência documental**, **interpretação** e **hipótese/recomendação**.
- Informar falha parcial, ausência de evidência e conflito entre versões.

### RF-07 — Catálogo e governança

- Manter no PostgreSQL o registro lógico de cada collection, sua finalidade, status, modelo, dimensão, distância, versão e escopo.
- Associar collections Qdrant a fontes e ingestões, mas não usar a existência no Qdrant como prova de publicação.
- Permitir `DRAFT`, `INDEXING`, `ACTIVE`, `PAUSED`, `REINDEXING`, `DEPRECATED` e `DELETED`.
- Impedir consulta de collections sem registro ativo no catálogo.
- Disponibilizar reconciliação administrativa entre catálogo e Qdrant, sem criar ou excluir dados automaticamente sem aprovação.

## 6. Arquitetura C4 — Contexto

```text
[Operador/Analista: pergunta e envia CSV]
        -- HTTPS autenticado --> [PreventIA Analysis Platform]

[Gestor: consulta sínteses e coleções autorizadas]
        -- HTTPS autenticado --> [PreventIA Analysis Platform]

[Curador: publica fontes e inicia ingestão]
        -- HTTPS autenticado --> [PreventIA Analysis Platform]

[PreventIA Analysis Platform]
        -- REST/HTTPS --> [LLM Gateway: interpretação e geração]

[PreventIA Analysis Platform]
        -- API Qdrant: consulta vetorial + filtros --> [Qdrant]

[PreventIA Analysis Platform]
        -- SQL --> [PostgreSQL: catálogo, ACL, jobs e auditoria]

[PreventIA Analysis Platform]
        -- objeto seguro --> [Object Storage: originais, texto e artefatos]

[PreventIA Analysis Platform]
        -- eventos assíncronos --> [Broker/Workers]

[PreventIA Analysis Platform]
        -- métricas/logs/traces --> [Observabilidade]
```

## 7. Arquitetura C4 — Containers

| Container | Tecnologia de referência | Responsabilidade | Comunicação |
|---|---|---|---|
| Streamlit Web App | Streamlit/Python | Chat, upload, cartão de collections, seleção de escopo, resultados e citações | HTTPS com API |
| Conversation API | FastAPI/Python | Autenticação, autorização, roteamento de intenção e composição da resposta | REST/HTTPS |
| Dataset Intake | Python, streaming e validadores | Quarentena, validação, perfilamento e normalização de CSV | Object storage + eventos |
| Tabular Analysis Engine | Polars/DuckDB | Plano seguro, agregações, perfilamento e proveniência | Job/API interna isolada |
| RAG Ingestion Worker | Python | Extração, chunking, embeddings, upsert e publicação controlada | Broker + storage + Qdrant |
| Embedding Service | Sentence Transformers ou FlagEmbedding | Gerar vetores com `BAAI/bge-m3` | RPC local ou HTTP interno |
| Retrieval Service | Python | Catálogo, ACL, consulta Qdrant, reranking, chunks e citações | SQL + API Qdrant |
| Qdrant | Qdrant self-hosted ou Cloud aprovado | Persistir e consultar vetores e payloads filtráveis | HTTP/gRPC interno com TLS |
| Metadata PostgreSQL | PostgreSQL | Catálogo lógico, identidade, ACL, fontes, versões, jobs e auditoria | SQL parametrizado |
| Object Storage | S3/Azure Blob ou equivalente | Arquivos originais, texto extraído e artefatos | API de objetos |
| Broker/Workers | RabbitMQ/SQS/Redis Queue | Jobs longos, retries e dead-letter | Mensageria assíncrona |
| LLM Gateway | Serviço/adapters Python | Timeout, retry, normalização, quotas e troca de provedor | HTTPS síncrono |
| Observability | OpenTelemetry + stack corporativa | Logs, métricas, traces e alertas | Exportação segura |

### Estratégia inicial de deployment

Começar com monólito modular Python, Streamlit, um worker, PostgreSQL, object storage e Qdrant em ambiente gerenciado ou self-hosted aprovado. Os módulos `RAG Ingestion`, `Embedding` e `Retrieval` devem possuir contratos internos estáveis para futura separação de deployment. A UI nunca terá credencial do Qdrant.

## 8. Modelo de dados Qdrant

### Configuração obrigatória da collection

```json
{
  "vectors": {
    "size": 1024,
    "distance": "Cosine",
    "on_disk": true
  },
  "embedding": {
    "embedding_model_name": "BAAI/bge-m3",
    "embedding_model_version": "pinned-by-deployment",
    "normalize_embeddings": true,
    "max_input_tokens": 8192
  }
}
```

O valor de `embedding_model_version` deve ser obtido do artefato efetivamente instalado e registrado no catálogo. O nome do modelo não pode ser alterado por input do usuário.

### Payload mínimo de um ponto

```json
{
  "chunk_id": "chk_opaque_id",
  "document_id": "doc_opaque_id",
  "document_version": 3,
  "collection_id": "col_opaque_id",
  "tenant_id": "tenant_opaque_id",
  "domain": "prevenção-de-perdas",
  "unit_ids": ["unidade_001"],
  "region_ids": ["sudeste"],
  "classification": "internal",
  "status": "published",
  "valid_from": "2026-01-01",
  "valid_to": null,
  "source_title": "Procedimento de inventário",
  "source_locator": "pagina-4/secao-2",
  "content_hash": "sha256:..."
}
```

O `text` completo do chunk deve ser recuperado por `chunk_id` em fonte controlada, ou armazenado no payload somente após avaliação de custo, privacidade e limite de tamanho. Em qualquer opção, o texto apresentado deve ser associado ao `content_hash` auditado.

### Convenção e estratégia de collections

- `collection_id` lógico e nome técnico Qdrant são identificadores distintos.
- Uma collection deve conter apenas vetores com o mesmo modelo, dimensão, normalização e métrica.
- Recomenda-se uma collection por corpus/domínio e modelo, com isolamento por payload quando a política permitir.
- Deve-se criar collection separada quando houver exigência de isolamento físico, retenção distinta ou incompatibilidade de embedding.
- Não criar uma collection por usuário, documento ou conversa; isso dificulta operação, consulta e governança.
- Trocas de modelo devem usar nova collection, reindexação e alias/ponteiro ativo; nunca sobrescrever vetores incompatíveis em produção.

## 9. Catálogo e API de collections

### Entidade lógica `knowledge_collection`

Campos mínimos:

```text
collection_id
display_name
description
qdrant_collection_name
tenant_id
domain
status
embedding_model_name
embedding_model_version
vector_size
distance
chunking_strategy_version
document_count
chunk_count
last_indexed_at
last_successful_sync_at
created_by
created_at
updated_at
```

ACL e escopos devem ser entidades relacionadas, com filtros por usuário, grupo, tenant, unidade, região e classificação. Não embutir uma lista fixa de usuários em cada chunk.

### Endpoints lógicos

- `GET /knowledge/collections` — lista paginada de collections autorizadas para o usuário.
- `GET /knowledge/collections/{collection_id}` — detalhes autorizados e status da collection.
- `POST /knowledge/collections/{collection_id}/query` — consulta RAG com pergunta e filtros permitidos.
- `POST /knowledge/sources` — cadastra fonte documental.
- `POST /knowledge/sources/{source_id}/ingestions` — inicia ingestão.
- `POST /knowledge/collections/{collection_id}/reindex` — solicita reindexação para perfil autorizado.
- `POST /conversation/messages` — pergunta geral, análise CSV, RAG ou híbrida.

### Resposta de `GET /knowledge/collections`

```json
{
  "items": [
    {
      "collection_id": "col_opaque_id",
      "display_name": "Políticas de Prevenção — Operações Brasil",
      "description": "Políticas vigentes de prevenção de perdas",
      "status": "ACTIVE",
      "document_count": 184,
      "last_successful_sync_at": "2026-10-18T10:30:00Z",
      "embedding_model_name": "BAAI/bge-m3",
      "embedding_dimension": 1024
    }
  ],
  "next_cursor": null
}
```

O endpoint não deve retornar URL interna, chave, nome do cluster, nomes de collections não autorizadas ou conteúdo de chunks.

## 10. Fluxos principais

### 10.1 Ingestão documental

1. Curador cadastra fonte e metadados.
2. API verifica permissão e grava a fonte no PostgreSQL.
3. Worker extrai texto e cria chunks versionados.
4. Embedding Service gera vetores usando `BAAI/bge-m3`.
5. Validador confirma dimensão `1024`, finitude, normalização e versão do modelo.
6. Worker faz upsert idempotente no Qdrant com payload filtrável.
7. Serviço de validação executa consultas de smoke test e confirma contagem/checksum.
8. Catálogo muda para `ACTIVE` somente após todos os critérios de publicação.

### 10.2 Listagem no chat

1. UI envia `GET /knowledge/collections` com a sessão autenticada.
2. API calcula escopo efetivo e consulta o catálogo, nunca o Qdrant diretamente.
3. O catálogo retorna somente collections `ACTIVE` autorizadas.
4. A UI renderiza cartão/mensagem no histórico e oferece seleção de collection.
5. A seleção grava apenas `collection_id` e escopo autorizado na sessão; não grava credenciais.
6. Auditoria registra usuário, quantidade e IDs lógicos retornados.

### 10.3 Consulta RAG

1. Usuário seleciona uma collection ou pergunta sobre conhecimento.
2. API identifica intenção e resolve o conjunto de collections permitido.
3. Embedding Service cria o vetor da pergunta com a mesma configuração do índice.
4. Retrieval Service monta filtro obrigatório de ACL, `status=published` e vigência.
5. Qdrant retorna candidatos por similaridade cosseno.
6. Retrieval Service aplica threshold, deduplicação, limite e reranking opcional.
7. Chunks autorizados são carregados e recebem IDs de citação.
8. LLM gera resposta somente a partir do contexto fornecido.
9. Response Guard verifica citações, escopo, instruções maliciosas e afirmações sem evidência.

## 11. Componentes do Retrieval Service

```text
[Collection Catalog Resolver]
        -> [Effective Scope/ACL Resolver]
        -> [Embedding Adapter: BAAI/bge-m3]
        -> [Qdrant Search Adapter]
             -> [Payload Filter Builder]
             -> [Score/Threshold Validator]
        -> [Chunk Repository]
        -> [Citation Builder]
        -> [Retrieval Audit Publisher]
```

### Responsabilidades críticas

- `Collection Catalog Resolver`: impede consulta a collection sem registro ativo.
- `Effective Scope/ACL Resolver`: calcula autorização por identidade, grupo, tenant, unidade, região e classificação.
- `Embedding Adapter`: fixa modelo, dimensão, normalização, timeout e versão do artefato.
- `Payload Filter Builder`: gera filtros parametrizados; nunca aceita filtro bruto vindo do usuário.
- `Qdrant Search Adapter`: encapsula SDK/HTTP, retries limitados, timeout, circuit breaker e métricas.
- `Score/Threshold Validator`: decide se há evidência suficiente; score não é tratado como verdade absoluta.
- `Citation Builder`: vincula chunk, documento, versão, localização e hash.
- `Retrieval Audit Publisher`: registra consulta técnica sem persistir segredo ou conteúdo excessivo.

## 12. Segurança, privacidade e operação do Qdrant

- Qdrant deve ficar em rede privada, com TLS, autenticação de serviço e política de firewall.
- A chave do Qdrant fica em secret manager; jamais no Streamlit, no navegador, no prompt ou no log.
- O serviço de aplicação usa identidade de serviço com permissões mínimas de leitura, busca, upsert e operação administrativa separadas.
- Operações destrutivas (`delete collection`, exclusão em massa e alteração de schema) exigem perfil operacional distinto e aprovação.
- O payload deve minimizar PII; preferir IDs tokenizados e referências controladas.
- Aplicar ACL tanto no catálogo quanto no filtro Qdrant no momento da busca.
- Não confiar em `collection_name`, `document_id` ou `tenant_id` informado pelo cliente sem resolver contra o catálogo e a sessão.
- Não retornar exceções do Qdrant ao usuário; mapear timeout, coleção inexistente, índice indisponível e conflito de schema para mensagens seguras.
- Fazer backup, teste de restauração e monitoramento de espaço/segmentos/latência.
- Medir e alertar `collection status`, falhas de upsert, pontos órfãos, divergência de contagem e atraso de indexação.
- Rotacionar credenciais e registrar acessos administrativos.
- Tratar documentos como instruções não confiáveis; o conteúdo nunca recebe prioridade sobre o system prompt.

## 13. Integrações e timeouts

| Interface | Padrão | Regra |
|---|---|---|
| Streamlit → Conversation API | REST/HTTPS | Perguntas, listagem e seleção de collection; resposta esperada em até 5 s para listagem |
| API → PostgreSQL | SQL parametrizado | Catálogo e ACL; sem SQL gerado pelo LLM |
| Retrieval → Qdrant | HTTP ou gRPC interno | Busca vetorial; timeout curto, retry apenas idempotente e circuit breaker |
| Ingestion Worker → Qdrant | HTTP/gRPC em lote | Upsert idempotente, batch limitado e dead-letter |
| Embedding Service → modelo | RPC local ou HTTP interno | Batches limitados, controle de memória e versão fixada |
| API → LLM Gateway | HTTPS síncrono | Timeout, quotas e resposta fundamentada |
| API → Worker | Mensageria assíncrona | Ingestão, reindexação, perfilamento e análises grandes |

## 14. Build vs. Buy vs. SaaS

| Capacidade | Recomendação | Critério |
|---|---|---|
| Orquestração, ACL e catálogo | Build modular | Regras são específicas do domínio e precisam de auditoria própria |
| Qdrant | SaaS gerenciado ou self-hosted aprovado | Escolher conforme residência de dados, SLA, operação e custo; manter adapter para portabilidade |
| Embeddings BGE-M3 | Build/operate como serviço interno | Reduz envio de documentos a terceiros e fixa qualidade; exige capacidade de CPU/GPU e governança de modelo |
| Extração de PDF/OCR | Buy/SaaS aprovado atrás de adapter | Time-to-market, qualidade e custo operacional; validar residência dos documentos |
| Object storage | SaaS/cloud gerenciado | Durabilidade, lifecycle e escalabilidade, condicionado à política de dados |
| LLM | Gateway com provedor aprovado | Permite trocar endpoint por custo, privacidade, latência e disponibilidade |
| Identidade e auditoria | SaaS corporativo | OIDC/OAuth2, RBAC/ABAC e integração com SIEM devem ser reutilizados |

## 15. Configuração mínima

```text
PREVENTIA_EMBEDDING_MODEL_NAME=BAAI/bge-m3
PREVENTIA_EMBEDDING_MODEL_VERSION=<artefato-fixado>
PREVENTIA_EMBEDDING_DIMENSION=1024
PREVENTIA_EMBEDDING_NORMALIZE=true
PREVENTIA_EMBEDDING_MAX_INPUT_TOKENS=8192
PREVENTIA_QDRANT_URL=<secret/configuração-do-ambiente>
PREVENTIA_QDRANT_API_KEY=<secret-manager>
PREVENTIA_QDRANT_TIMEOUT_SECONDS=3
PREVENTIA_QDRANT_COLLECTION_PAGE_SIZE=20
PREVENTIA_RAG_TOP_K=8
PREVENTIA_RAG_MIN_RELEVANCE=<limiar-aprovado>
PREVENTIA_RAG_MAX_CONTEXT_CHUNKS=8
PREVENTIA_RAG_RETENTION_DAYS=<política-aprovada>
METADATA_DATABASE_URL=<secret-manager>
OBJECT_STORAGE_BUCKET=<configuração-do-ambiente>
PREVENTIA_LLM_PROVIDER=<provedor-aprovado>
PREVENTIA_LLM_MODEL=<modelo-aprovado>
```

Segredos não podem ser versionados. A aplicação deve falhar no startup se a dimensão configurada divergir do contrato do modelo ou se a collection ativa tiver métrica/dimensão incompatível.

## 16. Observabilidade e qualidade

### Métricas técnicas

- latência p50/p95 de listagem, embedding, busca Qdrant, carregamento de chunks e geração;
- quantidade de collections autorizadas, vazias, inativas e com erro de sincronização;
- `top_k`, score mínimo/médio, taxa abaixo do threshold e taxa de “sem evidência”;
- throughput, latência e falhas de upsert;
- divergência entre `chunk_count` do catálogo e pontos válidos no Qdrant;
- uso de CPU/GPU/memória do Embedding Service;
- tokens, custo, timeout e erro do LLM;
- tamanho dos payloads, espaço e estado dos segmentos do Qdrant.

### Qualidade de retrieval e resposta

- Recall@K e MRR/NDCG em perguntas anotadas por especialistas.
- Precisão de citação: a fonte citada realmente sustenta a afirmação?
- Taxa de respostas sem evidência quando o corpus não contém resposta.
- Taxa de isolamento negativo: usuário sem ACL nunca recebe chunk de outro escopo.
- Regressão após alterar chunking, modelo, threshold, coleção ou prompt.
- Correção dos números CSV comparada com resultados de referência.

## 17. Riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Vazamento por filtro de ACL incompleto | Média | Alto | ACL no catálogo e no Qdrant, testes negativos, mínimo privilégio e auditoria |
| Embedding incompatível com a collection | Média | Alto | Schema fixo, startup validation, metadata do modelo e nova collection por migração |
| Prompt injection em documento/chunk | Alta | Alto | Conteúdo não confiável, prompt separado, allowlist de ferramentas e testes adversariais |
| Qdrant indisponível | Média | Alto | HA, timeout, circuit breaker, retry limitado, health check e resposta sem evidência |
| Coleções expostas por enumeração | Média | Médio | Listagem paginada, somente catálogo autorizado e nomes lógicos |
| Baixo recall do RAG | Média | Médio | BGE-M3, chunking avaliado, filtros corretos, busca híbrida futura e reranking |
| Crescimento de payload/índice | Média | Médio | Payload mínimo, object storage para texto, shards/segmentos conforme medição |
| Custo/latência de geração de embeddings | Média | Médio | Batch, cache por hash, processamento assíncrono e quotas |
| Divergência entre catálogo e Qdrant | Média | Alto | Reconciliação, checksums, contagem, estados de publicação e alarmes |
| Dados sensíveis enviados ao embedding/LLM | Média | Alto | Classificação, mascaramento, modelo interno, minimização e política de retenção |
| Números CSV inventados pela IA | Média | Alto | Engine determinística, provenance, response guard e testes de referência |

## 18. ADRs

### ADR-01 — Usar Qdrant como índice vetorial oficial

**Status:** Proposed  
**Contexto:** A solução precisa de busca semântica, filtros por payload, operação em lote e evolução para escala sem acoplar o domínio a SQL ou ao LLM.  
**Decisão:** Usar Qdrant para vetores e payloads de retrieval, atrás de um `Retrieval Service`; manter catálogo, ACL, ciclo de vida e auditoria no PostgreSQL.  
**Alternativas:**

- `pgvector`: menor número de componentes e boa simplicidade inicial, mas mistura mais diretamente catálogo/transação e retrieval em escala.
- Serviço vetorial SaaS: operação mais simples, porém dependência de fornecedor e restrições de residência/custo.
- Busca vetorial no LLM: não oferece governança, filtro de ACL ou controle de ciclo de vida.

**Consequências:** Ganha-se especialização em busca e filtros vetoriais; aumenta-se a responsabilidade por disponibilidade, reconciliação e operação do índice.

### ADR-02 — Fixar `BAAI/bge-m3` com vetores densos de 1024 dimensões

**Status:** Proposed  
**Contexto:** A recuperação precisa de um contrato reprodutível, com possibilidade de execução interna e controle sobre dados enviados a terceiros.  
**Decisão:** O primeiro índice usará `embedding_model_name="BAAI/bge-m3"`, dimensão `1024`, normalização habilitada e distância cosseno. Trocas de modelo gerarão nova collection e reindexação controlada.  
**Alternativas:**

- Embedding proprietário via SaaS: menor operação, mas custo, lock-in e possível envio de conteúdo sensível.
- Modelo menor: menor custo/latência, mas deve provar qualidade nos casos de negócio.
- Híbrido dense+sparse desde o MVP: potencialmente melhor para termos exatos, mas aumenta complexidade; fica como evolução após baseline.

**Consequências:** Requer operação do modelo, versionamento e capacidade computacional; oferece previsibilidade, portabilidade e menor dependência de provedor.

### ADR-03 — Listar collections por catálogo autorizado no chat

**Status:** Proposed  
**Contexto:** O usuário precisa saber quais bases pode consultar, mas consultar diretamente o endpoint administrativo do Qdrant exporia infraestrutura e poderia revelar collections restritas.  
**Decisão:** O chat consumirá `GET /knowledge/collections`, que consulta catálogo e ACL no PostgreSQL e retorna uma visão segura, paginada e auditável.  
**Alternativas:**

- UI consultar Qdrant diretamente: simples, mas viola isolamento e expõe credenciais/infraestrutura.
- Exibir lista fixa na UI: não acompanha ciclo de vida, permissões ou sincronização.
- Não exibir collections: mais simples, mas prejudica descoberta e usabilidade.

**Consequências:** Exige catálogo consistente e endpoint adicional; melhora governança, descoberta e segurança.

## 19. Estimativa

**Classificação:** XL para produção completa; G para MVP de CSV; G/XL para RAG com Qdrant, ACL, ingestão e avaliação.

| Fase | Percentual | Estimativa indicativa |
|---|---:|---:|
| Discovery e classificação de dados | 10% | 2–3 semanas |
| Design, contratos e PoC Qdrant/BGE-M3 | 15% | 3–4 semanas |
| Backend, ingestão, embeddings, retrieval e catálogo | 35% | 8–12 semanas |
| UI Streamlit, chat e cartão de collections | 20% | 4–6 semanas |
| QA, segurança e avaliação de IA | 15% | 3–5 semanas |
| DevOps, HA, observabilidade e deploy | 5% | 1–2 semanas |

Estimativa total indicativa: 4–6 meses com 4–6 pessoas, sujeita a disponibilidade de identidade, corpus autorizado, infraestrutura de embeddings e política de dados.

## 20. Roadmap

### Fase 1 — MVP de CSV

Upload, perfilamento, engine tabular, planos allowlisted, resultados reproduzíveis e proveniência. Sem dependência do Qdrant para validar o fluxo básico.

**Critério de saída:** dataset anonimizado real processado, números validados e nenhum caminho de execução arbitrária.

### Fase 2 — Fundação Qdrant e catálogo

Provisionar Qdrant, PostgreSQL de catálogo, Embedding Service com `BAAI/bge-m3`, collection de teste, schema, health checks, segredo, backup e endpoint autenticado de listagem.

**Critério de saída:** o chat lista somente collections autorizadas e os testes de dimensão, métrica e isolamento passam.

### Fase 3 — RAG controlado

Ingestão documental, chunking, embeddings, upsert idempotente, publicação, consulta, filtros ACL, citações e avaliação de retrieval.

**Critério de saída:** recall/precisão acordados, 100% dos testes negativos de autorização bloqueados e documento despublicado não recuperável em consulta nova.

### Fase 4 — Híbrido e estabilização

Consulta CSV + RAG, response guard, observabilidade completa, quotas, redaction, reindexação por alias, HA e testes adversariais.

**Critério de saída:** aprovação de segurança, qualidade, custo e operação para piloto controlado.

### Fase 5 — Escala e evolução

Reranking, busca lexical/híbrida, integração com SSO/RBAC/ABAC, collections por domínios com isolamento justificado, processamento maior e integrações somente leitura.

## 21. PoC técnico — máximo de 1–2 semanas

### PoC A — BGE-M3 + Qdrant

- **Hipótese:** `BAAI/bge-m3` recupera políticas e procedimentos relevantes com latência e custo compatíveis.
- **Testar:** geração local, dimensão 1024, normalização, distância cosseno, batch, persistência e consulta no Qdrant.
- **Sucesso:** 100% dos vetores com schema correto; recall@K mínimo definido pelo negócio; p95 de busca dentro da meta; nenhum conteúdo não autorizado nos testes.

### PoC B — Descoberta segura no chat

- **Hipótese:** o catálogo consegue listar collections ativas conforme ACL sem expor collections restritas ou credenciais.
- **Testar:** endpoint, paginação, escopo por usuário, collection vazia/inativa, revogação e renderização no Streamlit.
- **Sucesso:** testes positivos retornam somente o esperado e todos os testes negativos retornam lista vazia/filtrada sem revelar existência de recurso restrito.

O código do PoC é descartável. Não promover diretamente para produção; reimplementar com contratos, testes, segurança e observabilidade desta SPEC após decisão `go`.

## 22. Testes e critérios de aceite

### Testes obrigatórios

- Unidade: chunking, hash, idempotência, versão e metadados.
- Unidade: dimensão, normalização, modelo fixado e rejeição de vetor inválido.
- Integração: ingestão → embedding → upsert → consulta → citação.
- Qdrant: filtros por tenant/unidade/região/classificação, collection inativa, timeout, retry e divergência de schema.
- ACL: usuário autorizado, não autorizado, revogado e acesso a múltiplos escopos.
- Catálogo: paginação, coleção vazia, estado `REINDEXING`, collection órfã e reconciliação.
- Chat: listagem inicial, botão, pergunta em linguagem natural, seleção e persistência segura do escopo.
- Segurança: prompt injection em documento/CSV, enumeração, payload malformado, segredo em resposta e acesso direto à infraestrutura.
- CSV: parsing, tipos, nulos, fórmula, limites, plano inválido e números de referência.
- Performance: batch de embeddings, concorrência, p95 de retrieval, arquivos no limite e ingestão em lote.
- Resiliência: Qdrant indisponível, LLM indisponível, falha parcial de ingestão e dead-letter.

### Critérios de aceite

- [ ] Um usuário autorizado envia CSV e obtém análise reproduzível com proveniência.
- [ ] Uma fonte autorizada é ingerida e publicada em uma collection Qdrant com dimensão 1024 e distância cosseno.
- [ ] O embedding usado é registrado como `BAAI/bge-m3` e sua versão é rastreável.
- [ ] O chat lista collections disponíveis somente após aplicar identidade, ACL e status de publicação.
- [ ] A listagem não revela collections restritas, URL, chave ou detalhes administrativos do Qdrant.
- [ ] O usuário consegue selecionar uma collection listada e fazer pergunta com citação de documento, versão e localização.
- [ ] Collection inativa, documento expirado ou chunk não autorizado não aparece em consulta nova.
- [ ] Troca de modelo não sobrescreve vetores incompatíveis; cria novo índice/collection e passa por reindexação.
- [ ] Prompt injection não altera regras do sistema, filtros, permissões ou ferramentas.
- [ ] Falha do Qdrant resulta em mensagem segura e auditável, sem stack trace ou segredo.
- [ ] Consulta híbrida separa cálculo CSV, evidência RAG, interpretação e hipótese.

_Gerado por Arquiteto de Solução - Fusion Agent Platform_

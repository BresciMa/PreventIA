# SPEC — PreventIA Chatbot com Análise de CSV e RAG

**Status:** proposta para construção  
**Versão:** 2.0  
**Data:** 2026-10-20  
**Produto:** PreventIA — motor de prevenção de perdas usando IA  
**Baseline:** `.spec/PREVENTIA_CHATBOT.md` (versão 1.0)  
**Interface inicial:** aplicação web em Streamlit  
**Idioma inicial:** português do Brasil (pt-BR)

## 1. Objetivo e princípios arquiteturais

Evoluir o PreventIA para que o usuário possa:

1. enviar arquivos `.csv` com dados autorizados de prevenção de perdas;
2. validar e explorar o conjunto de dados com métricas calculadas de forma determinística;
3. fazer perguntas em linguagem natural e receber análises explicadas pela IA;
4. consultar uma base de conhecimento corporativa via RAG (Retrieval-Augmented Generation);
5. combinar dados do CSV e conhecimento documental na mesma resposta, sempre com indicação da origem das evidências.

A solução deve seguir estes princípios:

- **A IA interpreta; o motor de dados calcula.** Totais, médias, percentuais, agrupamentos e filtros devem ser executados por componentes determinísticos, e não inferidos pelo modelo.
- **Evidência antes de conclusão.** Respostas baseadas em documentos devem citar fonte, versão e trecho. Respostas baseadas em CSV devem indicar dataset, colunas, filtros e período utilizado.
- **Dados enviados pelo usuário são não confiáveis.** CSV, documentos, metadados e conteúdo recuperado podem conter instruções maliciosas ou dados sensíveis.
- **Separação entre dados tabulares e conhecimento documental.** O CSV será analisado por um motor tabular; não será automaticamente transformado em embeddings linha a linha.
- **Menor privilégio e retenção explícita.** O usuário só consulta datasets e documentos para os quais possui autorização, dentro do período de retenção definido.
- **Resposta auditável e humana.** O sistema não altera estoque, preços, pedidos, cadastros ou outros sistemas sem uma futura etapa explícita de aprovação.

## 2. Escopo da versão 2

### Incluído

- Todos os comportamentos de conversa, autenticação, persona, tratamento de erros e integração com LLM definidos na v1, revisados pelos requisitos desta versão.
- Upload de CSV pela interface de chat.
- Validação de extensão, tamanho, encoding, delimitador, cabeçalho, estrutura e conteúdo.
- Armazenamento temporário ou persistente conforme política de retenção.
- Perfilamento do dataset: colunas, tipos inferidos, valores ausentes, duplicidades, cardinalidade, estatísticas básicas e possíveis dados sensíveis.
- Perguntas em linguagem natural sobre um dataset selecionado.
- Geração de um plano de análise seguro e execução em engine tabular.
- Apresentação de tabelas, indicadores e gráficos simples, acompanhados de explicação em linguagem natural.
- Cadastro e indexação de fontes documentais autorizadas para RAG.
- Recuperação semântica e, quando necessário, híbrida (semântica + palavras-chave), com filtros de permissão e vigência.
- Respostas com citações de fontes documentais e indicação da proveniência dos dados tabulares.
- Consultas que combinem CSV, RAG e conhecimento geral do modelo, distinguindo cada evidência.
- Observabilidade, auditoria técnica, testes de segurança e avaliação de qualidade das respostas.

### Fora do escopo da primeira entrega da v2

- Treinamento ou fine-tuning de modelo.
- Execução de código Python arbitrário enviado pelo usuário ou gerado pelo LLM.
- Escrita em sistemas operacionais de loja, ERP, estoque, pedidos ou preços.
- Indexação automática de todas as linhas do CSV em um banco vetorial.
- Decisão autônoma de acusação de fraude ou ação disciplinar.
- Reconhecimento de imagem e multimodalidade.
- Colaboração em tempo real e compartilhamento externo de datasets.
- SSO e RBAC completo caso o provedor corporativo de identidade ainda não esteja disponível; a arquitetura deve manter um ponto de integração para isso.

## 3. Capacidade de negócio e personas

### Capacidade habilitada

**Análise assistida de perdas e consulta contextual de procedimentos.** A solução reduz o tempo entre a disponibilidade de dados e a identificação de anomalias, permitindo que operadores, analistas e gestores investiguem indicadores com linguagem natural e consultem políticas corporativas com rastreabilidade.

### Indicadores de negócio esperados

- tempo médio para analisar um arquivo e produzir uma hipótese;
- tempo para localizar uma política ou procedimento aplicável;
- quantidade de análises concluídas com evidência rastreável;
- redução de análises manuais repetitivas;
- taxa de respostas avaliadas como úteis por analistas;
- taxa de respostas sem evidência suficiente, alucinação ou necessidade de correção humana;
- incidência de exposição ou retenção indevida de dados sensíveis.

### Perfis

| Perfil | Interação | Permissões mínimas |
|---|---|---|
| Operador de loja | Envia CSV autorizado e pergunta sobre indicadores básicos | Ler e analisar datasets próprios ou compartilhados |
| Analista de prevenção | Investiga padrões, compara períodos e consulta procedimentos | Ler/analisar datasets autorizados e consultar RAG |
| Gestor | Consulta sínteses e recomendações com evidências | Ler análises e documentos autorizados |
| Curador de conhecimento | Publica, versiona e despublica fontes do RAG | Gerenciar fontes e metadados documentais |
| Administrador técnico | Configura provedores, limites, retenção e observabilidade | Administrar configurações; não deve acessar conteúdo sem justificativa |

## 4. Requisitos funcionais

### RF-01 a RF-09 — Conversa base

Aplicam-se os requisitos de inicialização, histórico, novo chat, controle de acesso, configuração de geração, persona, integração com LLM, apresentação da resposta e acessibilidade definidos na seção correspondente da SPEC v1. Na v2, o histórico deve também registrar referências a datasets, análises e citações sem armazenar o conteúdo integral de arquivos quando isso não for necessário.

### RF-10 — Upload de CSV

- Disponibilizar upload por componente visual e permitir associar o arquivo à conversa atual.
- Aceitar somente `.csv` conforme allowlist de extensão e tipo de conteúdo validado no servidor; a extensão informada pelo cliente não é suficiente.
- Aplicar limites configuráveis de tamanho, quantidade de linhas, colunas e tempo de processamento.
- Gerar um `dataset_id` opaco e associar o dataset ao usuário, sessão e política de retenção.
- Preservar o arquivo original de forma imutável, quando a política permitir, e gerar uma versão normalizada para análise.
- Detectar encoding e delimitador somente dentro de uma lista permitida; solicitar confirmação quando houver ambiguidade.
- Exigir cabeçalho ou oferecer mapeamento explícito de colunas, sem assumir nomes de negócio.
- Rejeitar ou colocar em quarentena arquivos corrompidos, vazios, com estrutura inconsistente ou que excedam limites.
- Nunca executar fórmulas, macros, comandos ou conteúdo de células como código.
- Neutralizar valores iniciados por `=`, `+`, `-` ou `@` ao exportar resultados para formatos que possam ser abertos como planilha, evitando CSV formula injection.

### RF-11 — Validação e perfilamento do dataset

- Exibir uma prévia limitada, sem carregar o arquivo inteiro na UI.
- Inferir tipos com confiança registrada: texto, inteiro, decimal, booleano, data/hora e nulo.
- Permitir correção manual de tipo e nome amigável antes da primeira análise.
- Calcular, no mínimo: quantidade de linhas, quantidade de colunas, nulos por coluna, duplicidades, cardinalidade, mínimo, máximo, média, mediana quando aplicável e distribuição de categorias limitada.
- Detectar possíveis identificadores pessoais, dados de contato, documentos, localização precisa e outras classes configuradas de dados sensíveis.
- Informar que inferência de dado sensível é indicativa e pode exigir confirmação humana.
- Não enviar o CSV inteiro ao LLM para obter o perfilamento.
- Exibir um resumo do dataset e pedir confirmação quando houver colunas ambíguas, datas inválidas ou conversões relevantes.

### RF-12 — Análise em linguagem natural

- Permitir perguntas como: “quais lojas tiveram maior índice de perdas no último mês?” ou “compare perdas por região”.
- Resolver a intenção em uma destas categorias: conversa geral, análise tabular, consulta RAG ou consulta híbrida.
- Gerar um plano de análise declarativo e validável, contendo dataset, colunas, filtros, agrupamentos, agregações, ordenação e limite de saída.
- Permitir apenas operações aprovadas pela engine de análise; nunca executar `eval`, `exec`, shell ou código arbitrário produzido pelo modelo.
- Executar o plano fora do processo da UI, com limite de CPU, memória, tempo e volume de resultado.
- Retornar resultado estruturado, parâmetros utilizados, advertências sobre qualidade dos dados e um resumo para o LLM.
- Usar o LLM somente para interpretar a pergunta, selecionar operações permitidas e explicar resultados calculados.
- Se a pergunta não puder ser respondida com os dados disponíveis, declarar a insuficiência e pedir o dado faltante.
- Não confundir correlação, anomalia estatística e causalidade; recomendações devem ser apresentadas como hipóteses quando não houver evidência causal.

### RF-13 — Visualização e proveniência da análise

- Exibir indicadores, tabela limitada e gráficos simples adequados ao tipo de resultado.
- Mostrar o nome do dataset, sua versão, timestamp, filtros, colunas e operação usada para formar o resultado.
- Mostrar o número de linhas consideradas e descartadas, quando aplicável.
- Permitir download apenas de resultados autorizados e sanitizados.
- Identificar valores estimados, arredondados, incompletos ou afetados por nulos.
- Não permitir que o LLM invente números: todo número exibido na resposta deve estar presente no resultado da engine ou em uma fonte citada.

### RF-14 — Cadastro e ingestão de fontes para RAG

- Permitir ao perfil autorizado cadastrar fontes documentais nos formatos inicialmente aprovados pela organização (por exemplo, PDF, Markdown, HTML ou TXT).
- Associar metadados obrigatórios: título, domínio, proprietário, versão, vigência, classificação de sensibilidade, unidades/regiões aplicáveis e permissões de leitura.
- Manter o arquivo original imutável e criar versões de ingestão identificáveis.
- Extrair texto, preservar estrutura relevante (título, seção, página ou posição) e marcar documentos sem texto extraível.
- Dividir o conteúdo em chunks com estratégia versionada, mantendo `document_id`, `document_version`, seção/página e hash do conteúdo.
- Gerar embeddings por um adaptador configurável e persistir somente após validação de sucesso.
- Indexar também termos para busca lexical quando a precisão exigir códigos, nomes de loja, políticas ou números.
- Permitir reprocessamento, despublicação e exclusão conforme retenção; documentos despublicados não podem ser recuperados por consultas novas.
- Isolar falha de uma fonte para não interromper a ingestão das demais.

### RF-15 — Consulta RAG

- Identificar intenção de consulta documental e aplicar primeiro filtros de autorização, escopo e vigência.
- Usar busca semântica, lexical ou híbrida conforme a configuração do domínio.
- Permitir reranking opcional para reduzir trechos irrelevantes antes da geração.
- Enviar ao LLM somente os trechos recuperados necessários, com identificadores de citação e instrução de não extrapolar a evidência.
- Responder “não encontrei evidência suficiente” quando o limiar de relevância não for atingido.
- Exibir citações clicáveis ou detalhadas com fonte, versão, seção/página e trecho de suporte.
- Impedir que instruções encontradas dentro de documentos sobrescrevam a persona, as políticas de segurança ou as regras do sistema.
- Aplicar controle de acesso novamente no momento da consulta, mesmo que os documentos tenham sido indexados anteriormente.

### RF-16 — Consulta híbrida CSV + RAG

- Quando a pergunta exigir dados e contexto, executar a análise tabular e a recuperação documental como etapas separadas.
- Passar ao LLM somente o resultado agregado da análise, seus metadados de proveniência e os chunks autorizados.
- Distinguir claramente na resposta: **resultado calculado**, **evidência documental**, **interpretação** e **hipótese/recomendação**.
- Não usar um documento para alterar silenciosamente os filtros ou números do CSV.
- Se as fontes discordarem, informar a divergência e priorizar a versão vigente conforme política configurada.

### RF-17 — Estado, retenção e exclusão

- Associar cada análise a `dataset_id`, versão, usuário, sessão e request/correlation ID.
- Exibir datasets disponíveis apenas para usuários autorizados.
- Permitir exclusão pelo proprietário ou administrador autorizado, respeitando retenção legal e auditoria mínima.
- Expirar arquivos temporários e resultados derivados automaticamente.
- Armazenar texto de conversa, datasets e documentos em políticas separadas; o token de acesso nunca pode ser persistido.

## 5. Arquitetura C4 — Contexto (nível 1)

Sistema central: **PreventIA Analysis Platform**, responsável por orquestrar conversa, análise tabular segura, consulta RAG e geração de resposta fundamentada.

```text
[Operador/Analista: pergunta e envia CSV]
        -- HTTPS, síncrono --> [PreventIA Analysis Platform]

[Gestor: consulta síntese e evidências]
        -- HTTPS, síncrono --> [PreventIA Analysis Platform]

[Curador: publica e versiona documentos]
        -- HTTPS, síncrono --> [PreventIA Analysis Platform]

[PreventIA Analysis Platform]
        -- HTTPS, síncrono --> [Provedor LLM: interpretação e geração]

[PreventIA Analysis Platform]
        -- objeto/stream seguro --> [Object Storage: CSVs, documentos e artefatos]

[PreventIA Analysis Platform]
        -- consulta SQL/engine --> [Store Tabular: dados normalizados e resultados]

[PreventIA Analysis Platform]
        -- busca vetorial + lexical --> [Índice RAG: embeddings e chunks autorizados]

[PreventIA Analysis Platform]
        -- OIDC/OAuth2, quando disponível --> [Provedor de Identidade Corporativo]

[PreventIA Analysis Platform]
        -- métricas/logs/traces --> [Plataforma de Observabilidade]
```

O fluxo de upload pode ser assíncrono após o recebimento inicial: a UI recebe um `dataset_id` e acompanha o status de validação. Uma pergunta simples pode ser síncrona; análises grandes e ingestão de documentos devem ser assíncronas.

## 6. Arquitetura C4 — Containers (nível 2)

| Container | Tecnologia de referência | Responsabilidade | Comunicação |
|---|---|---|---|
| Streamlit Web App | Streamlit/Python | Chat, upload, seleção de dataset, visualização e citações | HTTPS com API/orquestrador |
| API/Conversation Orchestrator | Python, FastAPI ou camada de serviço equivalente | Autorização, roteamento de intenção, composição de contexto e estado | REST/HTTPS; eventos para jobs |
| Dataset Intake | Python, streaming e validadores CSV | Receber, validar, quarentenar e registrar datasets | Upload para object storage; eventos assíncronos |
| Tabular Analysis Engine | Python com Polars/Pandas e DuckDB conforme volume | Perfilamento, planos seguros, agregações e resultados | API interna ou job isolado; leitura de artefato imutável |
| LLM Gateway | Python | Adaptar provedores, timeout, retry, normalização e telemetria | HTTPS síncrono |
| RAG Ingestion Worker | Python | Extrair, segmentar, gerar embeddings e indexar documentos | Fila assíncrona; object storage; índice RAG |
| Retrieval Service | Python | Busca híbrida, filtros ACL, vigência e reranking | API interna; índice vetorial/lexical |
| Metadata Relational DB | PostgreSQL ou equivalente | Usuários, permissões, datasets, versões, jobs, fontes e auditoria | SQL parametrizado |
| Object Storage | S3/Azure Blob ou equivalente | Arquivos originais, normalizados e artefatos | API de objetos com URLs temporárias |
| Tabular Store | Parquet + DuckDB inicialmente; warehouse posteriormente se necessário | Consulta eficiente sem carregar tudo em memória | Leitura local/objeto; somente leitura durante análise |
| Vector/Lexical Index | pgvector + full-text inicialmente, ou serviço gerenciado | Embeddings, chunks e busca lexical com metadados | API/SQL com filtro de autorização |
| Job Broker/Worker Runtime | Redis Queue, SQS, RabbitMQ ou equivalente | Processamentos longos, retries e dead-letter | Mensageria assíncrona |
| Observability Stack | OpenTelemetry + solução corporativa | Métricas, logs estruturados, traces e alertas | Exportação segura |

### Estratégia de implantação recomendada

Para o MVP, começar como um monólito modular Python com Streamlit e serviços de domínio separados, PostgreSQL, object storage, DuckDB/Parquet e um worker. O contrato entre módulos deve permitir extrair posteriormente o `Tabular Analysis Engine`, `RAG Ingestion Worker` e `Retrieval Service` para deploy independente. Microserviços só devem ser adotados quando volume, isolamento de segurança ou cadência de escala justificar o custo operacional.

## 7. C4 — Componentes do Orchestrator (nível 3)

```text
[HTTP/Streamlit Controllers]
        -> [AuthZ Policy]
        -> [Intent Router]
        -> [Conversation Orchestrator]
             -> [Dataset Analysis Use Case]
             -> [RAG Query Use Case]
             -> [Hybrid Query Use Case]
        -> [Evidence Composer]
        -> [Response Formatter]

[Dataset Analysis Use Case]
        -> [Analysis Plan Validator]
        -> [Tabular Engine Adapter]
        -> [Provenance Builder]

[RAG Query Use Case]
        -> [Access Scope Resolver]
        -> [Retrieval Adapter]
        -> [Citation Builder]

[Hybrid Query Use Case]
        -> [Dataset Analysis Use Case]
        -> [RAG Query Use Case]
        -> [Evidence Composer]

[Conversation Orchestrator]
        -> [Prompt Builder]
        -> [LLM Gateway]
        -> [Response Guard]

[Todos os casos de uso]
        -> [Dataset/Document Repositories]
        -> [Audit and Metrics Publisher]
```

### Componentes críticos

- **Intent Router:** classifica a solicitação sem dar autoridade ao LLM para ignorar regras de segurança.
- **Analysis Plan Validator:** valida dataset, colunas, operadores, limites, tipos e custo estimado do plano.
- **Tabular Engine Adapter:** executa operações allowlisted, isolado da UI e sem interpretar código arbitrário.
- **Access Scope Resolver:** calcula permissões efetivas para cada dataset, documento e chunk antes da recuperação.
- **Evidence Composer:** associa cada afirmação à saída tabular ou a uma citação documental.
- **Response Guard:** remove ou bloqueia respostas que apresentem números sem proveniência, revelem segredos ou transformem hipótese em fato.
- **Prompt Builder:** compõe persona, instruções de segurança, histórico resumido, resultado calculado e evidências autorizadas.
- **Repositories/Adapters:** infraestrutura; não devem conter regras de negócio nem expor credenciais.

## 8. Fluxos principais

### 8.1 Upload e preparação do CSV

1. UI solicita upload e envia o arquivo pelo canal autenticado.
2. Intake valida tamanho, tipo, nome, checksum e limites preliminares.
3. O arquivo é salvo em quarentena; o nome original não é usado como identificador de segurança.
4. O worker detecta encoding/delimitador, valida estrutura e produz perfilamento.
5. O sistema grava metadados e gera versão normalizada em Parquet ou formato equivalente.
6. O usuário visualiza o perfilamento e confirma mapeamentos ambíguos.
7. O dataset muda para `READY` ou `REJECTED`, com motivo seguro e auditável.

Estados mínimos: `RECEIVED`, `SCANNING`, `PROFILED`, `READY`, `REJECTED`, `EXPIRED`, `DELETED`.

### 8.2 Pergunta sobre CSV

1. O usuário seleciona um dataset `READY` e envia a pergunta.
2. O sistema valida autorização e classifica a intenção.
3. O LLM ou componente de regras propõe um plano declarativo limitado.
4. O validador rejeita colunas inexistentes, operadores não permitidos, custo excessivo e tentativas de execução de código.
5. A engine executa o plano em ambiente com limites.
6. O resultado e a proveniência são enviados ao gerador de resposta.
7. A resposta mostra números calculados, advertências e parâmetros usados.

### 8.3 Consulta RAG

1. O usuário faz uma pergunta documental.
2. O sistema resolve identidade, unidade, região, perfil e permissões.
3. O retrieval filtra por autorização, documento publicado e vigência.
4. A busca híbrida recupera candidatos e o reranker seleciona trechos relevantes.
5. O LLM recebe trechos identificados, instruções anti-injeção e formato obrigatório de citação.
6. O guard valida presença de evidências e o formatter apresenta as citações.

### 8.4 Consulta híbrida

O sistema executa os fluxos 8.2 e 8.3 separadamente, compõe as evidências e só então gera a explicação. Falha parcial deve ser explícita: por exemplo, entregar o resultado do CSV e informar que nenhuma política autorizada foi encontrada.

## 9. Contratos de dados e APIs

### Dataset

```json
{
  "dataset_id": "ds_opaque_id",
  "version": 1,
  "status": "READY",
  "display_name": "perdas lojas setembro",
  "row_count": 125000,
  "columns": [
    {"name": "loja", "type": "string", "nullable": false},
    {"name": "data", "type": "datetime", "nullable": false},
    {"name": "valor_perda", "type": "decimal", "nullable": true}
  ],
  "profile": {"missing_values": {}, "warnings": []},
  "retention_expires_at": "ISO-8601",
  "provenance": {"checksum": "sha256:..."}
}
```

### Plano de análise permitido

```json
{
  "dataset_id": "ds_opaque_id",
  "select": ["loja", "valor_perda"],
  "filters": [{"column": "data", "operator": "between", "value": ["2026-09-01", "2026-09-30"]}],
  "group_by": ["loja"],
  "aggregations": [{"column": "valor_perda", "function": "sum", "alias": "total_perda"}],
  "order_by": [{"column": "total_perda", "direction": "desc"}],
  "limit": 20
}
```

As funções, operadores, limites e tipos válidos devem ser definidos por allowlist versionada. O JSON é contrato de domínio; não deve ser convertido diretamente em SQL sem validação e parametrização.

### Resultado com proveniência

```json
{
  "analysis_id": "an_opaque_id",
  "dataset_id": "ds_opaque_id",
  "plan_hash": "sha256:...",
  "rows_considered": 120340,
  "result": {"columns": [], "rows": []},
  "warnings": ["12,4% dos valores de valor_perda são nulos"],
  "provenance": {"dataset_version": 1, "executed_at": "ISO-8601"}
}
```

Endpoints lógicos, sujeitos ao padrão de API adotado:

- `POST /datasets` — iniciar upload e retornar `dataset_id`;
- `GET /datasets/{dataset_id}` — consultar status, perfilamento e permissões;
- `POST /datasets/{dataset_id}/analyses` — executar pergunta/plano validado;
- `GET /analyses/{analysis_id}` — consultar resultado ou status do job;
- `POST /knowledge/sources` — cadastrar fonte autorizada;
- `POST /knowledge/sources/{source_id}/ingestions` — iniciar ingestão/versionamento;
- `POST /knowledge/query` — executar recuperação RAG com citações;
- `POST /conversation/messages` — orquestrar pergunta geral, CSV ou híbrida.

## 10. Segurança, privacidade e governança de dados

- Usar autenticação corporativa e RBAC/ABAC assim que disponível; token de serviço não deve ser usado como substituto de identidade de usuário em produção.
- Aplicar autorização por dataset, documento, unidade, região, classificação e vigência em todas as leituras.
- Armazenar arquivos com criptografia em repouso, TLS em trânsito, URLs temporárias e bloqueio de acesso público.
- Executar antivírus/antimalware e validação de conteúdo antes de disponibilizar qualquer arquivo.
- Manter arquivos e jobs fora do processo da UI; aplicar limites de memória, CPU, tempo, linhas, resultado e concorrência.
- Não permitir `eval`, `exec`, imports dinâmicos, shell, acesso à rede ou leitura arbitrária de caminhos pelo plano de análise.
- Tratar prompt injection em CSV, documentos e resultados recuperados como conteúdo não confiável.
- Não indexar dados sensíveis sem classificação e aprovação. Quando o caso de uso exigir, mascarar ou tokenizar PII antes de enviar conteúdo ao LLM.
- Não enviar linhas brutas ao LLM por padrão; preferir agregados, amostras minimizadas e colunas estritamente necessárias.
- Redigir logs e traces para remover tokens, conteúdo de arquivos, PII, prompts e respostas completas por padrão.
- Registrar auditoria de upload, acesso, análise, download, publicação, despublicação e exclusão.
- Definir retenção por tipo: arquivo original, versão normalizada, resultado, conversa, chunks e logs.
- Aplicar rate limit, quotas por usuário e limites de custo do LLM/embeddings.
- Validar saída antes de exportar para planilha para evitar formula injection.

## 11. Padrões de integração e comunicação

| Interface | Padrão | Justificativa |
|---|---|---|
| UI → API/orquestrador | REST/HTTPS síncrono | Login, metadados, perguntas pequenas e acompanhamento de status |
| Upload → Intake | Multipart/HTTPS ou upload direto com URL temporária | Evita transportar arquivos grandes pela camada de chat |
| Intake → workers | Mensageria assíncrona | Perfilamento e normalização podem durar mais que o timeout da UI |
| Orchestrator → LLM Gateway | REST/HTTPS síncrono com timeout | Resposta necessária para a conversa; retry apenas em falhas transitórias |
| Orchestrator → Tabular Engine | RPC interno ou job assíncrono | Isola carga e permite controle de recursos |
| Orchestrator → Retrieval Service | REST/gRPC interno | Busca com resposta rápida e contrato estável |
| Ingestion Worker → embeddings | HTTPS síncrono por lote | Gera vetores controlando custo e limites do provedor |
| Worker → índice RAG | SQL/API de índice | Persistência de chunks, embeddings e metadados filtráveis |
| Jobs → status UI | Polling inicialmente; webhook/event stream futuramente | Simplicidade no MVP, evolução para atualização em tempo real |

## 12. Build vs. Buy vs. SaaS

| Capacidade | Build | Buy | SaaS | Recomendação e critério |
|---|---|---|---|---|
| Upload, catálogo e permissões de datasets | Controle e integração máximos; maior manutenção | Pode limitar o modelo de autorização | Implantação rápida, porém dados ficam sob contrato do fornecedor | **Build modular**: é parte do domínio e exige política própria de acesso/retensão |
| Engine de CSV e agregações | Flexibilidade com Python; risco de desempenho se mal isolada | Ferramentas prontas podem ter custo/licença | Warehouses/serverless escalam rápido, com custo variável | **Build usando engines maduras** (Polars/DuckDB) no MVP; migrar para warehouse se volume justificar |
| Armazenamento de arquivos | Operação e HA próprias | Appliance/licença | Object storage gerenciado, durável e escalável | **SaaS/cloud gerenciado**, condicionado a residência, classificação e contrato de dados |
| Banco vetorial e busca híbrida | Controle e portabilidade | Produto on-premise especializado | Serviço gerenciado reduz operação | **Começar com PostgreSQL + pgvector/full-text**; adotar serviço dedicado apenas por escala/latência |
| Embeddings e LLM | Controle de modelo, custo e dados; maior esforço | Licença pode facilitar operação | Time-to-market e qualidade inicial melhores; lock-in e custo recorrente | **Gateway abstrato + provedor aprovado**; avaliar modelo privado quando PII ou custo exigir |
| OCR/extrator documental | Diferencial e controle difíceis | Produto especializado | API SaaS rápida, com risco de envio de documentos | **SaaS aprovado ou componente maduro**, atrás de adapter e com política de dados |
| Identidade e auditoria | Alto custo para manter corretamente | Integração com produto existente | IdP corporativo/SIEM gerenciado | **Buy/SaaS corporativo**, integrando por OIDC/OAuth2 e exportando auditoria |

## 13. Configuração mínima

```text
PREVENTIA_PROVIDER=fusion
PREVENTIA_MODEL=<modelo-aprovado>
PREVENTIA_MAX_TOKENS=2000
PREVENTIA_TEMPERATURE=0.70
PREVENTIA_REQUEST_TIMEOUT_SECONDS=60
PREVENTIA_MAX_HISTORY_TOKENS=<limite-aprovado>
PREVENTIA_DATASET_MAX_BYTES=<limite-aprovado>
PREVENTIA_DATASET_MAX_ROWS=<limite-aprovado>
PREVENTIA_DATASET_RETENTION_DAYS=<política-aprovada>
PREVENTIA_ALLOWED_ANALYSIS_FUNCTIONS=sum,avg,count,min,max,median,distinct
PREVENTIA_RAG_TOP_K=<limite-aprovado>
PREVENTIA_RAG_MIN_RELEVANCE=<limiar-aprovado>
PREVENTIA_RAG_RETENTION_DAYS=<política-aprovada>
PREVENTIA_PERSONA_PATH=<caminho-da-persona>
OBJECT_STORAGE_BUCKET=<configuração-do-ambiente>
METADATA_DATABASE_URL=<secret-manager>
VECTOR_INDEX_URL=<configuração-do-ambiente>
```

Nenhum valor secreto deve ser versionado. Limites de arquivo, custo e retenção devem ser diferentes por ambiente e aprovados pela governança de dados.

## 14. Observabilidade e qualidade de IA

### Métricas técnicas

- tempo e status de upload, perfilamento, análise, retrieval e geração;
- p50/p95 de latência por etapa;
- filas, retries, dead-letter e jobs expirados;
- uso de CPU/memória e tamanho dos datasets;
- tokens, custo estimado e erros por provedor;
- quantidade de chunks recuperados, score mínimo e taxa de “sem evidência”.

### Métricas de qualidade

- precisão de citações e cobertura de evidência;
- correção dos números contra resultados de referência;
- taxa de planos inválidos ou corrigidos pelo validador;
- taxa de respostas que distinguem fato, cálculo e hipótese;
- avaliação humana por perfil e por tipo de pergunta;
- regressão de qualidade após troca de modelo, chunking, embeddings ou prompt.

Deve existir um conjunto versionado de perguntas anonimizadas com respostas esperadas ou critérios de avaliação. Não avaliar somente fluência: a qualidade deve medir correção, rastreabilidade, segurança e utilidade operacional.

## 15. Riscos arquiteturais e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| CSV malicioso ou excessivamente grande derruba o processo | Média | Alto | Quarentena, scanner, streaming, limites, worker isolado e circuit breaker |
| Vazamento de PII para LLM ou índice RAG | Média | Alto | Classificação, mascaramento, ACL em duas camadas, minimização e logs redigidos |
| Números incorretos por alucinação | Média | Alto | Engine determinística, plano validado, proveniência, response guard e testes de referência |
| Prompt injection em documento ou célula | Alta | Alto | Conteúdo não confiável, separação de instruções, allowlist de ferramentas e avaliação adversarial |
| Filtro de autorização aplicado tarde demais | Média | Alto | ACL antes do retrieval, filtros no índice, testes de isolamento e auditoria |
| Baixa qualidade de OCR/chunking reduz recall do RAG | Média | Médio | PoC, busca híbrida, reranking, metadados estruturais e conjunto de avaliação |
| Gargalo de memória na análise | Média | Alto | Parquet, DuckDB/Polars, execução limitada, amostragem e migração para warehouse |
| Lock-in de LLM/embeddings/vector store | Média | Médio | Interfaces de adapter, exportação de documentos/chunks e ADR de portabilidade |
| Custo imprevisível de tokens e embeddings | Média | Médio | Quotas, sumarização/agregação antes do LLM, cache controlado e alertas |
| Resultado derivado fica inconsistente com o CSV original | Baixa/Média | Alto | checksum, versões imutáveis, `plan_hash`, dataset version e proveniência |
| Disponibilidade do provedor externo | Média | Alto | timeout, retry limitado, circuit breaker, fallback aprovado e mensagens claras |

## 16. ADRs principais

### ADR-01 — Separar cálculo tabular da geração de linguagem

**Status:** Proposed  
**Contexto:** Modelos de linguagem podem produzir explicações plausíveis, mas não são uma fonte confiável para calcular agregações em CSV.  
**Decisão:** Executar análises em uma engine tabular com plano declarativo validado; usar o LLM para interpretar intenção e explicar o resultado.  
**Alternativas:**

- Enviar o CSV ao LLM: implementação inicial simples, mas custo, limite de contexto, privacidade e correção são inadequados.
- Gerar e executar código Python: flexível, mas cria risco de execução arbitrária e dificuldade de governança.
- Usar somente consultas manuais: seguro, porém não atende a linguagem natural.

**Consequências:** Aumenta a complexidade de orquestração e do validador, mas torna números reproduzíveis, auditáveis e testáveis.

### ADR-02 — Usar RAG com índice híbrido e ACL por metadados

**Status:** Proposed  
**Contexto:** Políticas e procedimentos contêm termos exatos, códigos, versões e linguagem semântica; somente busca vetorial pode perder correspondências literais e pode expor fontes indevidas.  
**Decisão:** Indexar chunks com embeddings e índice lexical, aplicar filtros de autorização/vigência antes da recuperação e exigir citações na resposta.  
**Alternativas:**

- Busca vetorial somente: melhor para paráfrases, pior para códigos e controle de escopo.
- Busca textual somente: simples e precisa para termos, pior para perguntas sem os mesmos termos do documento.
- Fine-tuning do LLM: não resolve controle de versão nem citações e aumenta o custo de atualização.

**Consequências:** Exige pipeline de ingestão, versionamento e avaliação de retrieval, mas melhora precisão, governança e explicabilidade.

### ADR-03 — Manter um gateway abstrato para LLM e embeddings

**Status:** Proposed  
**Contexto:** O projeto pode alternar entre endpoint corporativo, provedor externo ou modelo privado por custo, privacidade, disponibilidade e política de dados.  
**Decisão:** Isolar autenticação, payload, retries e normalização em adapters; o domínio depende de contratos internos.  
**Alternativas:**

- Integrar diretamente na UI: menor código inicial, mas alto acoplamento e risco de credenciais.
- Fixar um único provedor: simplifica a operação, mas aumenta lock-in e dificulta contingência.
- Hospedar modelo próprio desde o início: maior controle, mas adiciona operação e pode atrasar o MVP.

**Consequências:** Exige contrato de compatibilidade e testes por provedor, mas facilita substituição, fallback aprovado e controle de custo.

## 17. Estimativa de complexidade e esforço

### Classificação

- **CSV com análise assistida:** G alto, aproximadamente 8–12 semanas, 3–5 pessoas.
- **RAG com ingestão, ACL, citações e avaliação:** G/XL, aproximadamente 10–16 semanas, 4–6 pessoas.
- **V2 completa com ambas as capacidades em produção:** XL, aproximadamente 4–6 meses, incluindo segurança, governança, operação e estabilização.

Estimativa indicativa para a entrega completa, sujeita a PoC, disponibilidade de identidade, storage e provedor de IA:

| Fase | Percentual | Esforço relativo |
|---|---:|---:|
| Discovery e classificação de dados | 10% | 2–3 semanas |
| Design e contratos | 15% | 3–4 semanas |
| Backend, intake, engine e RAG | 35% | 7–10 semanas |
| UI Streamlit e visualizações | 20% | 4–6 semanas |
| QA, segurança e avaliação de IA | 15% | 3–5 semanas |
| DevOps, observabilidade e deploy | 5% | 1–2 semanas |

As frentes podem sobrepor-se, mas a análise de dados sensíveis, o contrato de identidade e a decisão sobre storage/vector store são dependências de caminho crítico.

## 18. Roadmap de implementação

### Fase 1 — MVP de análise CSV

**Entregáveis:** upload autenticado, validação, perfilamento, armazenamento, dataset `READY`, perguntas básicas, planos allowlisted, agregações, tabela/gráfico e proveniência.  
**Containers:** Streamlit, Orchestrator modular, Dataset Intake, Tabular Engine, Metadata DB, Object Storage e LLM Gateway.  
**Entrada:** limites de arquivo, classificação de dados e política de retenção aprovados.  
**Saída:** pelo menos um fluxo real anonimizado com números reproduzíveis e sem execução de código arbitrário.

### Fase 2 — RAG controlado

**Entregáveis:** cadastro de fontes, ingestão assíncrona, versionamento, chunking, embeddings, índice híbrido, filtros ACL, citações e tela de fontes.  
**Containers:** RAG Ingestion Worker, Retrieval Service, índice vetorial/lexical e Job Broker.  
**Entrada:** corpus documental autorizado, proprietário definido e conjunto de perguntas de avaliação.  
**Saída:** limiar acordado de recall/precisão e zero acesso cruzado nos testes de autorização.

### Fase 3 — Consultas híbridas e estabilização

**Entregáveis:** fluxo CSV + RAG, response guard, comparação temporal, observabilidade completa, quotas, alertas, redaction e testes adversariais.  
**Entrada:** Fases 1 e 2 operando com dados representativos por pelo menos duas semanas.  
**Saída:** aprovação de segurança, qualidade e operação para piloto controlado.

### Fase 4 — Escala e integração

**Entregáveis:** SSO/RBAC/ABAC corporativo, processamento de arquivos maiores, warehouse quando necessário, integração somente leitura com sistemas internos, exportação governada e HA.  
**Entrada:** volume, latência e custo medidos no piloto.  
**Saída:** metas de SLA/SLO e governança aprovadas para produção ampliada.

## 19. Escopo de PoC técnico

Executar antes do comprometimento integral do time, com duração máxima de 1–2 semanas.

### PoC A — CSV e plano seguro

- **Hipótese:** um modelo consegue converter perguntas representativas em planos allowlisted, e a engine retorna números corretos em datasets de tamanhos previstos.
- **Tecnologias:** Python, DuckDB/Polars, adapter do LLM e conjunto de CSVs anonimizados.
- **Sucesso:** 95% ou mais dos casos de referência produzem resultado correto após validação; nenhum caso executa código arbitrário; p95 de consulta dentro da meta acordada.

### PoC B — RAG com controle de acesso

- **Hipótese:** chunking, embeddings e busca híbrida recuperam a política vigente e respeitam unidade/região/perfil.
- **Tecnologias:** extrator documental aprovado, PostgreSQL/pgvector ou índice equivalente, embeddings e reranking opcional.
- **Sucesso:** limiar de recall@k definido pelo negócio; 100% dos testes negativos de autorização bloqueados; citações apontam para versão e trecho corretos.

O código do PoC é descartável e não deve ser promovido diretamente para produção. Após decisão go, a implementação deve ser reescrita com contratos, testes, segurança e observabilidade desta SPEC.

## 20. Testes e critérios de aceite

### Testes obrigatórios

- Unidade: parsing, encoding, delimitador, tipos, nulos, duplicidades, limites e classificação de dados sensíveis.
- Unidade: validador de plano, allowlist de operadores, parametrização e limites de custo.
- Integração: upload → perfilamento → dataset `READY` → análise com engine fake/real controlada.
- Segurança: CSV com fórmulas, payloads grandes, traversal, prompt injection, conteúdo malformado e tentativa de código.
- RAG: chunking, versionamento, documento vigente, documento expirado, ACL positiva/negativa e citações.
- Híbrido: divergência entre CSV e documento, falha parcial e ausência de evidência.
- LLM: timeout, 4xx, 429, 5xx, resposta sem texto, plano inválido e troca de provedor.
- Regressão: histórico, novo chat, ausência de token e comportamentos da v1.
- Performance: arquivos no limite, concorrência, p95 da análise, ingestão em lote e recuperação.
- Privacidade: nenhum token, PII desnecessária, linha bruta ou conteúdo sensível em logs e prompts fora da política.

### Critérios de aceite da v2

- [ ] Um usuário autorizado consegue enviar um CSV válido e acompanhar seu processamento.
- [ ] CSV inválido, excedente ou malicioso é rejeitado/quarentenado sem derrubar a aplicação.
- [ ] O sistema apresenta perfilamento e solicita confirmação para ambiguidades relevantes.
- [ ] Uma pergunta suportada produz plano validado, resultado reproduzível e proveniência do dataset.
- [ ] Nenhum número da resposta depende de aritmética feita pelo LLM.
- [ ] Usuário sem permissão não consegue consultar dataset, documento, chunk ou resultado de outro escopo.
- [ ] Uma fonte RAG publicada e vigente é recuperada com citação de versão e trecho.
- [ ] Documento expirado/despublicado não aparece em consultas novas.
- [ ] Prompt injection em CSV/documento não altera as regras do sistema nem executa ação indevida.
- [ ] Consulta híbrida separa resultado calculado, evidência documental, interpretação e hipótese.
- [ ] Retenção, exclusão, quotas, logs redigidos e auditoria estão verificáveis.
- [ ] Testes de referência medem correção numérica, qualidade de retrieval e fidelidade das citações.

## 21. Migração da v1 e decisões pendentes

### Migração

1. Preservar a persona, o contrato de LLM e os testes de conversa da v1.
2. Extrair a integração atual para o `LLM Gateway` antes de adicionar CSV/RAG.
3. Introduzir identidade e autorização no orquestrador, sem tratar token de serviço como identidade final.
4. Implementar CSV como novo fluxo isolado; não misturar linhas brutas ao histórico textual.
5. Implementar RAG com corpus pequeno e controlado antes de habilitar documentos corporativos amplos.
6. Habilitar consulta híbrida somente depois dos critérios das Fases 1 e 2.

### Decisões que precisam ser confirmadas pelo negócio e segurança

- tamanho máximo, volume esperado e periodicidade dos CSVs;
- classes de dados proibidas, retenção e residência dos dados;
- fontes documentais iniciais, proprietários, vigência e modelo de permissões;
- provedor LLM/embeddings autorizado e política de envio de dados a terceiros;
- metas de latência, concorrência, custo por análise e disponibilidade;
- taxonomia oficial de perdas e definições dos indicadores;
- necessidade de aprovação humana para recomendações e exportações.

## 22. Entrega e controle de versão

Este arquivo é a fonte única da especificação da v2. A v1 permanece como baseline histórico. Alterações em contratos, limites, políticas de dados, provedor, modelo de autorização ou critérios de aceite devem gerar uma nova revisão deste documento antes da implementação correspondente.

_Gerado por Arquiteto de Solução — Fusion Agent Platform_

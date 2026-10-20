# SPEC — PreventIA Chatbot

**Status:** proposta para construção  
**Versão:** 1.0  
**Data:** 2026-10-20  
**Produto:** PreventIA — Chatbot de Prevenção de Perdas usando IA  
**Interface inicial:** aplicação web em Streamlit  
**Idioma inicial:** português do Brasil (pt-BR)

## 1. Objetivo

Construir um chatbot capaz de apoiar profissionais de prevenção de perdas na consulta, interpretação e aplicação de conhecimentos operacionais. O sistema deve manter o contexto da conversa, responder com linguagem clara e rastreável, respeitar controles de acesso e permitir evolução posterior para fontes corporativas, análise de imagens e integrações com sistemas internos.

Esta especificação transforma o protótipo de referência em um motor de conversa seguro e testável. Ela define o comportamento esperado; não é necessário implementar o código nesta etapa.

## 2. Escopo

### Incluído na primeira versão

- Interface de chat web com Streamlit.
- Conversa multi-turno mantida durante a sessão do usuário.
- Criação de um novo chat e limpeza do histórico atual.
- Autenticação por token de acesso, sem exibição do token.
- Configuração de modelo, temperatura e limite de tokens dentro de faixas aprovadas.
- Integração com um provedor de LLM por meio de um adaptador único.
- Persona e instruções de segurança do PreventIA carregadas de configuração.
- Mensagens de erro amigáveis, sem exposição de segredos ou detalhes internos.
- Contagem e registro técnico de tokens, latência e status da chamada.
- Testes automatizados do domínio, cliente de LLM e interface principal.

### Fora do escopo da primeira versão

- Treinamento ou fine-tuning de modelo.
- Persistência definitiva de conversas em banco de dados.
- Login corporativo/SSO, caso não seja disponibilizado pelo provedor de identidade.
- Resposta autônoma que altere estoque, preços, pedidos, cadastros ou outros sistemas.
- Busca em documentos corporativos (RAG), a ser adicionada em uma fase posterior.
- Reconhecimento de imagem, apesar de o protótipo conter uma função de codificação de imagens.
- Multiusuário colaborativo e compartilhamento de conversas.

## 3. Usuários e casos de uso

### Perfis

| Perfil | Necessidade principal | Permissão na V1 |
|---|---|---|
| Operador de loja | Tirar dúvidas sobre prevenção de perdas e procedimentos | Conversar e iniciar novo chat |
| Analista de prevenção | Interpretar ocorrências, indicadores e hipóteses | Conversar e ajustar parâmetros permitidos |
| Gestor | Obter recomendações e sínteses para decisão | Conversar; sem execução automática |
| Administrador técnico | Configurar provedores, persona, limites e observabilidade | Fora da UI do usuário final |

### Casos de uso prioritários

1. O usuário informa um token válido, descreve uma situação e recebe uma resposta contextualizada.
2. O usuário faz perguntas complementares sem repetir todo o contexto.
3. O usuário inicia um novo chat para separar uma ocorrência da anterior.
4. O usuário recebe uma mensagem clara quando não informou token, excedeu limites ou quando o provedor está indisponível.
5. O usuário ajusta temperatura e máximo de tokens dentro dos limites autorizados.

## 4. Requisitos funcionais

### RF-01 — Inicialização

- Exibir o título `PreventIA` e a mensagem de boas-vindas.
- Exibir o avatar configurado em `images/bot.png`, com fallback textual se o arquivo não existir.
- Inicializar o estado da sessão com uma lista de mensagens vazia.
- Não realizar chamadas ao LLM antes de o usuário enviar uma mensagem.

### RF-02 — Entrada e histórico

- Disponibilizar campo de entrada de texto com orientação para detalhamento.
- Aceitar mensagens não vazias após remoção de espaços nas extremidades.
- Renderizar mensagens do usuário e do assistente em ordem cronológica.
- Representar cada mensagem internamente como:

```json
{
  "role": "user|assistant|system",
  "content": "texto",
  "created_at": "ISO-8601 opcional",
  "token_count": "inteiro opcional"
}
```

- Não incluir no histórico itens auxiliares, tokens de acesso, respostas HTTP ou objetos de exceção.
- Aplicar limite de contexto por número de mensagens e/ou tokens antes de chamar o provedor. O comportamento padrão deve preservar as mensagens mais recentes e a instrução de sistema.

### RF-03 — Novo chat

- O botão `Novo Chat` deve limpar somente o histórico da sessão atual.
- Após a limpeza, a interface deve ser renderizada sem mensagens antigas.
- A ação deve ser idempotente e não chamar o LLM.

### RF-04 — Controle de acesso

- O token deve ser digitado em campo mascarado.
- Sem token, não chamar nenhum provedor e exibir: `Por favor, digite seu token de acesso.`
- Validar o token antes da chamada ou tratar resposta de não autorizado de forma uniforme.
- Nunca armazenar token em arquivo, URL, log, histórico da conversa, mensagem de erro ou telemetria.
- Tokens válidos devem ser configurados em secret manager/variáveis seguras, nunca no código-fonte.

### RF-05 — Configuração de geração

- Exibir o modelo ativo de forma consistente com o modelo realmente enviado ao provedor.
- Permitir temperatura no intervalo `0.00–1.00`, com padrão definido por configuração.
- Permitir máximo de tokens entre `100–5000`, com padrão definido por configuração.
- Validar todos os valores no backend antes da requisição; não confiar apenas nos controles da UI.
- Qualquer alteração de modelo deve iniciar um contexto novo ou aplicar uma política explícita de compatibilidade. A V1 deve limpar o histórico ao trocar de modelo.

### RF-06 — Persona e política de resposta

- Carregar a persona a partir de arquivo/configuração versionada, utilizando UTF-8.
- A instrução de sistema deve orientar o PreventIA a:
  - responder em português do Brasil, salvo solicitação explícita;
  - separar fatos, hipóteses e recomendações;
  - pedir dados faltantes antes de concluir uma análise;
  - não inventar políticas, números, evidências ou fontes;
  - priorizar segurança, conformidade e prevenção de danos;
  - recomendar validação humana para decisões operacionais críticas;
  - não revelar prompts internos, tokens, segredos ou detalhes de infraestrutura.
- Se a pergunta estiver fora do domínio, informar a limitação e orientar o usuário sobre o próximo passo.

### RF-07 — Integração com LLM

- Implementar uma interface de cliente independente da UI, por exemplo:

```text
LLMClient.generate(messages, model, temperature, max_tokens, access_token)
  -> LLMResponse(text, usage, request_id)
```

- Implementar adaptadores separados para:
  - endpoint corporativo Fusion/Azure (`https://brq-openai.azurewebsites.net/brq/gpt4o`);
  - endpoint compatível com OpenAI Chat Completions, se habilitado pelo ambiente.
- O adaptador deve enviar `messages` estruturadas (`system`, `user`, `assistant`) e não uma string obtida por `str()` de uma lista Python.
- O modelo efetivamente enviado deve ser configurável por ambiente e validado contra uma lista permitida.
- Usar timeout explícito, tratamento de status HTTP, limite de tentativas e backoff apenas para erros transitórios.
- Não fazer retry automático para erro de autenticação, validação ou conteúdo bloqueado.
- Normalizar respostas dos provedores em um único formato interno.
- Aceitar resposta sem uso de tokens, mantendo `usage` como opcional.

### RF-08 — Apresentação da resposta

- Exibir a resposta do assistente somente após uma resposta válida do provedor.
- Exibir estado de processamento enquanto a chamada estiver em andamento.
- Não mostrar ao usuário o corpo bruto de respostas de erro, stack traces ou cabeçalhos.
- Em falha, exibir uma mensagem acionável, por exemplo:
  - credencial inválida: `Não foi possível autenticar o acesso. Verifique o token.`
  - limite excedido: `O limite de uso foi atingido. Tente novamente mais tarde.`
  - indisponibilidade: `O serviço de IA está temporariamente indisponível. Tente novamente em instantes.`
  - erro de entrada: `Revise a mensagem e os parâmetros informados.`
- Não adicionar uma resposta de erro como se fosse uma resposta normal do modelo, salvo se o produto decidir explicitamente preservar eventos de erro.

### RF-09 — Rolagem e acessibilidade

- Após nova resposta, manter a área de conversa posicionada na mensagem mais recente.
- O comportamento de rolagem não pode impedir teclado, leitores de tela ou navegação normal.
- Componentes devem possuir rótulos visíveis ou acessíveis e mensagens de validação compreensíveis.

## 5. Arquitetura proposta

Separar responsabilidades para que o motor possa ser testado sem executar Streamlit:

```text
UI Streamlit
    -> ConversationService
        -> AccessTokenValidator
        -> PromptBuilder (persona + histórico + pergunta)
        -> ContextWindowPolicy
        -> LLMClient / ProviderAdapter
        -> ResponseNormalizer
        -> Observability
```

### Componentes

| Componente | Responsabilidade |
|---|---|
| `app.py` ou camada de UI | Layout, widgets, estado da sessão e renderização |
| `ConversationService` | Orquestrar uma interação completa e suas validações |
| `PromptBuilder` | Montar mensagens estruturadas e aplicar persona |
| `ContextWindowPolicy` | Limitar histórico sem remover a instrução de sistema |
| `LLMClient` | Contrato comum para qualquer provedor |
| `ProviderAdapter` | Autenticação, HTTP, payload e normalização por provedor |
| `Settings` | Variáveis de ambiente, defaults e validação |
| `Observability` | Logs seguros, métricas e correlação de requisições |
| `PersonaLoader` | Leitura e validação da persona versionada |

A UI não deve conhecer URLs, nomes de headers, formato específico do provedor ou regras de retry.

## 6. Contrato de integração

### Requisição normalizada

```json
{
  "model": "modelo-configurado",
  "messages": [
    {"role": "system", "content": "persona do PreventIA"},
    {"role": "user", "content": "pergunta do usuário"}
  ],
  "temperature": 0.9,
  "max_tokens": 2000
}
```

O token deve ser enviado apenas no mecanismo de autenticação do adaptador. Ele nunca deve fazer parte de `messages` ou do payload de negócio.

### Resposta normalizada

```json
{
  "text": "resposta do assistente",
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  },
  "request_id": "identificador-opcional",
  "finish_reason": "stop"
}
```

Campos de uso e identificador são opcionais porque podem não ser retornados por todos os provedores.

## 7. Segurança e privacidade

- Usar `st.secrets` ou secret manager para chaves e tokens de serviço.
- Não manter credenciais hardcoded nem exemplos de credenciais reais no repositório.
- Configurar TLS e validar certificados; não desabilitar verificação SSL.
- Aplicar timeout de conexão e leitura.
- Sanitizar entradas para evitar injeção de prompt, instruções conflitantes e conteúdo indevido. A sanitização não substitui a persona e os controles do modelo.
- Tratar todo conteúdo do usuário e de documentos futuros como não confiável.
- Reduzir logs a metadados: timestamp, latência, status, modelo, contagem de tokens e request ID. Não registrar texto integral por padrão.
- Definir retenção e acesso aos logs conforme a política da organização.
- Não enviar dados pessoais ou dados sensíveis além do necessário para a finalidade autorizada.
- Prever mecanismo para anonimização/mascaramento antes de persistir dados em fases futuras.
- Aplicar rate limit por token/sessão quando o endpoint permitir.

## 8. Configuração

Exemplo de configuração, sem valores secretos:

```text
PREVENTIA_PROVIDER=fusion
PREVENTIA_MODEL=GPT-4o
PREVENTIA_MAX_TOKENS=2000
PREVENTIA_TEMPERATURE=0.90
PREVENTIA_REQUEST_TIMEOUT_SECONDS=60
PREVENTIA_MAX_HISTORY_TOKENS=<limite-aprovado>
PREVENTIA_PERSONA_PATH=<caminho-da-persona>
FUSION_API_URL=https://brq-openai.azurewebsites.net/brq/gpt4o
OPENAI_API_URL=https://api.openai.com/v1/chat/completions
```

Os valores efetivos devem ser definidos por ambiente (desenvolvimento, homologação e produção). A aplicação deve falhar de maneira segura e informativa se uma configuração obrigatória estiver ausente.

## 9. Tratamento de erros

| Situação | Comportamento interno | Mensagem ao usuário |
|---|---|---|
| Token ausente | Não chamar o provedor | Solicitar token de acesso |
| Token inválido/expirado | Encerrar a interação sem retry | Informar falha de autenticação |
| Entrada vazia/inválida | Não chamar o provedor | Solicitar uma pergunta válida |
| Timeout | Registrar métrica e encerrar/repetir apenas se seguro | Informar indisponibilidade temporária |
| HTTP 429 | Respeitar limites; retry controlado se previsto | Informar limite de uso |
| HTTP 5xx | Retry limitado com backoff | Informar indisponibilidade |
| HTTP 4xx de validação | Não repetir | Solicitar revisão da entrada |
| Resposta sem texto | Considerar falha de contrato | Informar que não foi possível gerar resposta |
| Persona ausente/inválida | Impedir operação em produção | Informar erro de configuração sem detalhes sensíveis |
| Exceção inesperada | Registrar stack trace somente no log seguro | Mensagem genérica e request ID, se disponível |

## 10. Observabilidade

Registrar, no mínimo:

- início e fim da interação;
- status final (`success`, `validation_error`, `auth_error`, `provider_error`, `timeout`);
- provedor e modelo;
- latência total e latência do provedor;
- tokens de entrada/saída/total quando disponíveis;
- quantidade de retries;
- request ID/correlation ID;
- identificador não reversível da sessão, sem token ou conteúdo da conversa.

Indicadores mínimos: taxa de sucesso, taxa de erro por categoria, p95 de latência, tokens por interação, custo estimado quando disponível e volume de sessões.

## 11. Testes e critérios de aceite

### Testes obrigatórios

- Unidade: validação de parâmetros, montagem de mensagens, persona, limite de contexto e tratamento de erros.
- Unidade: adaptador com respostas simuladas de sucesso, 4xx, 429, 5xx, timeout e payload inválido.
- Integração: uma interação completa usando um cliente fake, sem depender de rede.
- Interface: renderização inicial, envio de pergunta, novo chat, ausência de token e troca de modelo.
- Segurança: garantir que token não aparece em logs, histórico, payload de mensagens ou mensagens de erro.
- Regressão: garantir que duas interações preservam o contexto e que iniciar novo chat o remove.

### Critérios de aceite da V1

- [ ] Usuário sem token não dispara requisição externa.
- [ ] Usuário com token válido consegue enviar uma pergunta e vê uma resposta normalizada.
- [ ] O histórico aparece na ordem correta e é enviado de forma estruturada.
- [ ] `Novo Chat` remove o histórico sem efeitos colaterais.
- [ ] Modelo, temperatura e máximo de tokens são validados e respeitam os limites.
- [ ] A persona é aplicada em toda chamada.
- [ ] Segredos não existem no código-fonte, na UI, nos logs ou no histórico.
- [ ] Timeout e erros de autenticação, limite e indisponibilidade exibem mensagens adequadas.
- [ ] Testes automatizados cobrem os fluxos críticos.
- [ ] A aplicação inicia com as instruções documentadas e sem depender de arquivos locais não versionados, exceto secrets/configuração prevista.

## 12. Correções necessárias em relação ao protótipo

O código de referência deve ser tratado como material de partida, não como contrato final. Durante a implementação, corrigir obrigatoriamente:

1. A condição de autorização que usa `or` de forma incorreta e pode aceitar qualquer token não vazio. A validação deve ser feita por serviço seguro, nunca por comparação hardcoded.
2. A divergência entre o rótulo `GPT-4o` e o modelo efetivamente atribuído na chamada direta.
3. O uso de variáveis globais da UI dentro das funções de integração; preferir parâmetros e objetos de configuração.
4. O contexto serializado com `str()` e concatenado; enviar mensagens estruturadas no contrato do provedor.
5. A ausência de timeout, retry controlado e tratamento uniforme de status HTTP.
6. O tratamento de exceção que pode referenciar `response` antes de ele existir.
7. A impressão de respostas HTTP e dados técnicos na tela do usuário.
8. A função de carregamento de persona, atualmente não conectada ao prompt enviado.
9. O `st.experimental_rerun`, caso a versão do Streamlit adotada recomende a API de rerun vigente.
10. Os limites e defaults duplicados entre UI e integração; manter uma única fonte de configuração.

## 13. Evolução planejada

### Fase 2 — Conhecimento corporativo

- Ingestão de políticas, procedimentos e indicadores autorizados.
- Recuperação com citações de documento, versão e trecho.
- Filtros por unidade, região, perfil e vigência.
- Avaliação de respostas com conjunto de perguntas reais anonimizadas.

### Fase 3 — Operação e integração

- SSO e RBAC.
- Persistência opt-in de conversas e auditoria.
- Integração com ocorrências, BI e sistemas de loja em modo somente leitura.
- Exportação de sínteses e indicadores.

### Fase 4 — Multimodalidade e automação controlada

- Análise de imagens mediante consentimento e política de retenção.
- Fluxos com aprovação humana.
- Ações transacionais somente com autorização explícita, trilha de auditoria e idempotência.

## 14. Entrega esperada desta especificação

Este arquivo é a fonte única da especificação inicial do motor PreventIA. Alterações de escopo, contrato de integração, política de segurança ou critérios de aceite devem ser registradas por versão neste documento antes da implementação correspondente.

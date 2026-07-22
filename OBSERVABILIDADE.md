# Observabilidade - Bebidas Scan

Atualizado em: 2026-07-20

## Diagnostico

Pontos encontrados antes da revisão:

- Logs em texto simples via `logging.basicConfig`.
- Alguns eventos de auditoria e segurança estavam em strings soltas, por exemplo `login_sucesso id_usuario=...`.
- Ausencia de `requestId` por requisição.
- `userId` nem sempre estava disponível automaticamente nos logs de rotas autenticadas.
- Falhas de integração com Open Food Facts retornavam `None` silenciosamente.
- Blocos `except IntegrityError` em operações críticas retornavam erro sem log estruturado.
- Fluxos LGPD sensíveis, como exportação CSV e anonimização, tinham pouca rastreabilidade.
- Não havia teste garantindo máscara de senha/token/e-mail em logs.

## Implementado

### Logs estruturados JSON

O backend agora usa `JsonFormatter` em `backend/app/logging_config.py`.

Campos padrão:

- `timestamp`
- `level`
- `logger`
- `message`
- `requestId`
- `userId`
- `event`
- `action`
- campos específicos do evento

### Contexto por requisição

O middleware HTTP cria ou propaga `X-Request-ID`.

Cada resposta recebe:

```text
X-Request-ID
```

Cada requisição gera evento:

```text
request_completed
```

com:

- método
- caminho
- status HTTP
- duração em ms
- cliente

### UserId automático

Rotas autenticadas passam a preencher o contexto de log com o `id_usuario` resolvido pelo token.

### Sanitização / Data Masking

Campos sensíveis são mascarados automaticamente:

- senha
- password
- tokens
- authorization
- refresh token
- access token
- JWT
- secret
- CSRF
- cookies
- e-mail
- identidade de login
- CPF
- telefone
- data de nascimento

Valor mascarado:

```text
***MASKED***
```

### Eventos cobertos

Autenticação:

- `usuario_registrado`
- `login_sucesso`
- `login_falhou`
- `logout`
- `rate_limit`
- `auth_lockout`

HTTP:

- `request_completed`
- `request_too_large`
- `unhandled_exception`

Bebidas:

- `bebida_criada`
- `bebida_editada`
- `edicao_bebida_negada`
- `bebida_criacao_conflito`
- `bebida_edicao_conflito`
- `bebida_codigo_nao_encontrado`
- `bebida_open_food_facts_conflito`

Open Food Facts:

- `open_food_facts_http_error`
- `open_food_facts_status_invalido`
- `open_food_facts_json_invalido`
- `open_food_facts_produto_nao_encontrado`
- `open_food_facts_produto_ignorado`

LGPD/privacidade:

- `lgpd_aceita`
- `dados_exportados_csv`
- `anonimizacao_confirmacao_falhou`
- `conta_anonimizada`

Avaliações e preços:

- `avaliacao_salva`
- `preco_registrado`

## Níveis de log

Padrão adotado:

- `info`: eventos esperados de negócio e auditoria.
- `warn`: ações negadas, rate limit, conflitos esperados, falhas externas recuperáveis.
- `error`: exceções não tratadas, conflitos inesperados que exigem investigação.
- `fatal/critical`: reservado para falhas de inicialização, indisponibilidade de banco ou corrupção de estado.

## Sobre Winston/Pino

Winston e Pino são excelentes para aplicações Node.js.

Como este backend é Python/FastAPI, a implementação equivalente foi feita com:

- `logging` padrão do Python
- formatter JSON próprio
- `contextvars` para `requestId` e `userId`
- sanitização centralizada

Se futuramente houver um serviço Node.js, recomenda-se Pino por padrão:

- alta performance
- JSON nativo
- redaction built-in
- integração fácil com Loki, ELK, Datadog e Cloudflare Logs

Exemplo conceitual em Pino:

```js
const logger = pino({
  level: process.env.LOG_LEVEL || "info",
  redact: [
    "req.headers.authorization",
    "password",
    "senha",
    "access_token",
    "refresh_token",
    "email",
    "cpf"
  ]
})
```

## Próximos passos recomendados

- Enviar logs para um coletor central, como Grafana Loki, ELK, Datadog ou Better Stack.
- Criar métrica para taxa de `login_falhou`, `rate_limit` e `unhandled_exception`.
- Criar alerta para `error` e `critical`.
- Separar logs de auditoria e segurança em sinks/retencões diferentes.
- Incluir `traceId` se futuramente houver múltiplos serviços.
- Configurar rotação/retencão de logs conforme LGPD.
- Remover ou reduzir logs de acesso do Uvicorn em produção, mantendo os logs estruturados da aplicação.


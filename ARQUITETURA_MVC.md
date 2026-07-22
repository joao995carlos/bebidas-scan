# Arquitetura MVC Do Bebidas Scan

Estado atual: o backend usa um MVC pratico com camada de services.

## Camadas

### Models

Arquivos responsaveis por representar dados e persistencia.

- `backend/app/models.py`: modelos SQLAlchemy e relacionamentos.
- `backend/app/schemas.py`: contratos de entrada e saida da API com Pydantic.
- `backend/app/database.py`: conexao, sessao e base do banco.
- `backend/app/migrations.py`: migracoes leves executadas na inicializacao.

### Controllers

Arquivos responsaveis por expor rotas HTTP e conectar requisicoes aos services.

- `backend/app/controllers/*_controller.py`: ponto publico de roteamento usado por `main.py`.
- `backend/app/routes_*.py`: endpoints FastAPI. Nos modulos ja migrados, ficam finos e delegam regra de negocio.

### Views

Arquivos responsaveis por renderizar HTML e componentes de tela.

- `backend/app/views/admin_views.py`: layout, headers de seguranca, dashboard, tabelas e formularios do painel admin.
- `backend/app/views/web_views.py`: layout web, home, scanner, detalhe de bebida, formularios de bebida, login, cadastro, LGPD, privacidade, favoritos e avaliacoes.

### Services

Arquivos responsaveis por regra de negocio, validacoes de fluxo, persistencia coordenada e logs de auditoria.

- `backend/app/services/auth_service.py`: cadastro, login, refresh token e logout.
- `backend/app/services/bebida_service.py`: cadastro, edicao, busca por nome/codigo, separacao de bebida e cachaca, Open Food Facts.
- `backend/app/services/perfil_service.py`: status LGPD, aceite, exportacao CSV e anonimização de conta.
- `backend/app/services/avaliacao_service.py`: salvar e listar avaliacoes do usuario.
- `backend/app/services/favorito_service.py`: listar, adicionar e remover favoritos.
- `backend/app/services/preco_service.py`: registrar e listar precos.
- `backend/app/services/privacidade_service.py`: politica de privacidade e termos de uso.
- `backend/app/services/admin_service.py`: metricas, usuarios, acoes administrativas e consultas administrativas.
- `backend/app/services/web_service.py`: autenticacao web, LGPD web, exportacao, anonimização, favoritos, avaliacoes e consultas simples da interface web.

### Infraestrutura E Apoio

- `backend/app/security.py`: senhas, JWT e refresh tokens.
- `backend/app/logging_config.py`: logs estruturados JSON, contexto e mascaramento de dados sensiveis.
- `backend/app/rate_limit.py`: limitacao de tentativas de autenticacao.
- `backend/app/open_food_facts.py`: integracao externa.
- `backend/app/lgpd.py`: regras LGPD compartilhadas.
- `backend/app/dependencies.py`: dependencias FastAPI, autenticacao do usuario e permissoes.

## Regra Para Novas Funcionalidades

1. Criar ou alterar modelos em `models.py` e contratos em `schemas.py`.
2. Colocar regra de negocio em `backend/app/services`.
3. Manter `routes_*.py` pequeno, apenas recebendo parametros HTTP e chamando o service.
4. Exportar o router em `backend/app/controllers`.
5. Registrar o controller em `main.py`.
6. Adicionar logs estruturados no service quando houver acao importante, falha de seguranca, auditoria ou integracao externa.

## Proximos Passos Recomendados

- Avaliar migracao futura de views Python para templates Jinja2 se o HTML crescer mais.
- Dividir `models.py` e `schemas.py` por dominio quando o projeto crescer mais.

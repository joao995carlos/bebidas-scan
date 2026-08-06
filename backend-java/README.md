# Bebidas Scan API Java

Estrutura inicial do backend Java/Spring Boot para migrar o backend atual em FastAPI sem interromper o app existente.

## Stack

- Java 21
- Spring Boot
- Spring Web
- Spring Data JPA
- Spring Security
- Bean Validation
- PostgreSQL
- Actuator
- Flyway preparado, desativado por padrao

## Como rodar

Com PostgreSQL local ou o `db` do `docker-compose.yml` principal:

```powershell
cd "D:\Arquivos\Documentos\Bebidas Scan\backend-java"
mvn spring-boot:run
```

Health check:

```text
GET http://localhost:8080/health
```

## Estrutura

```text
src/main/java/br/com/bebidasscan/api/
  auth/              # login, JWT, refresh token e reset de senha
  usuario/           # usuarios e perfil base
  bebida/            # bebidas, cachaca e busca
  avaliacao/         # avaliacoes
  favorito/          # favoritos
  preco/             # precos
  perfil/            # LGPD, exportacao e anonimizar conta
  privacidade/       # politica e termos
  admin/             # painel/admin
  integration/       # Open Food Facts, Resend e APIs externas
  config/            # configuracoes Spring
  health/            # endpoints basicos
```

## Estrategia de migracao

1. Manter o FastAPI como referencia.
2. Manter os mesmos endpoints usados pelo app Flutter.
3. Migrar primeiro autenticacao e `/me`.
4. Depois migrar bebidas, favoritos, avaliacoes e precos.
5. Por ultimo migrar LGPD, e-mails, admin e web views.

## Banco de dados

As entidades JPA foram mapeadas para as tabelas atuais:

- `usuario`
- `refresh_token`
- `password_reset_token`
- `bebida`
- `cachaca`
- `avaliacao`
- `favorito`
- `preco`

Por padrao, `spring.jpa.hibernate.ddl-auto=validate`. Assim o Spring valida o schema existente, mas nao tenta alterar o banco automaticamente.

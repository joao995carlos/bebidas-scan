import os
import tempfile
import uuid
import logging
import re

os.environ["JWT_SECRET_KEY"] = "x" * 64
os.environ["WEB_CSRF_SECRET"] = "w" * 64
os.environ["ADMIN_USERNAME"] = "admin_test"
os.environ["ADMIN_PASSWORD"] = "senha_admin_test"
os.environ["AUTH_RATE_LIMIT_MAX_ATTEMPTS"] = "3"
os.environ["AUTH_RATE_LIMIT_WINDOW_SECONDS"] = "60"
os.environ["AUTH_RATE_LIMIT_IDENTITY_MAX_ATTEMPTS"] = "2"
os.environ["AUTH_RATE_LIMIT_IDENTITY_WINDOW_SECONDS"] = "300"
os.environ["AUTH_LOCKOUT_SECONDS"] = "900"
os.environ["MAX_REQUEST_BODY_BYTES"] = "500"

fd, db_path = tempfile.mkstemp(suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = "sqlite:///" + db_path.replace("\\", "/")

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.logging_config import JsonFormatter  # noqa: E402
from app.main import app  # noqa: E402


Base.metadata.create_all(bind=engine)
client = TestClient(app)


def csrf_from(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, html[:1000]
    return match.group(1)


def registrar_usuario(email: str, senha: str = "Senha@123") -> dict:
    nome_usuario = email.split("@", 1)[0].replace(".", "_").replace("-", "_")[:70]
    resposta = client.post(
        "/auth/registrar",
        json={
            "nome": "Usuario QA",
            "nome_usuario": nome_usuario,
            "email": email,
            "senha": senha,
            "data_nascimento": "1990-01-01",
            "aceitou_privacidade": True,
            "aceitou_termos": True,
            "marketing_consentimento": False,
        },
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_rota_protegida_sem_token_e_token_invalido():
    assert client.get("/perfil/me").status_code in {401, 403}
    resposta = client.get("/perfil/me", headers=auth_headers("token-invalido"))
    assert resposta.status_code == 401


def test_rate_limit_login_senha_errada():
    email = f"rate-{uuid.uuid4().hex}@example.com"
    registrar_usuario(email)

    status_codes = [
        client.post("/auth/login", json={"email": email, "senha": "errada"}).status_code
        for _ in range(4)
    ]

    assert 401 in status_codes
    assert status_codes[-1] == 429

    from app.rate_limit import _attempts

    _attempts.clear()


def test_rate_limit_por_identidade_mesmo_com_ips_diferentes():
    from app.rate_limit import _attempts, _blocked_until

    _attempts.clear()
    _blocked_until.clear()
    email = f"identity-{uuid.uuid4().hex}@example.com"
    registrar_usuario(email)

    status_codes = []
    for idx in range(3):
        resposta = client.post(
            "/auth/login",
            headers={"x-forwarded-for": f"10.0.0.{idx + 1}"},
            json={"email": email, "senha": "errada"},
        )
        status_codes.append(resposta.status_code)

    assert status_codes == [401, 401, 429]
    _attempts.clear()
    _blocked_until.clear()


def test_usuario_nao_edita_bebida_de_outro_usuario():
    dono = registrar_usuario(f"dono-{uuid.uuid4().hex}@example.com")
    outro = registrar_usuario(f"outro-{uuid.uuid4().hex}@example.com")

    criada = client.post(
        "/bebidas",
        headers=auth_headers(dono["access_token"]),
        json={"nome": "Bebida do dono", "tipo": "cachaca"},
    )
    assert criada.status_code == 200, criada.text

    resposta = client.patch(
        f"/bebidas/{criada.json()['id_bebida']}",
        headers=auth_headers(outro["access_token"]),
        json={"nome": "Tentativa indevida"},
    )
    assert resposta.status_code == 403


def test_preco_negativo_e_avaliacao_fora_do_limite():
    usuario = registrar_usuario(f"validacao-{uuid.uuid4().hex}@example.com")
    headers = auth_headers(usuario["access_token"])
    bebida = client.post(
        "/bebidas",
        headers=headers,
        json={"nome": "Bebida validacao", "tipo": "cachaca"},
    ).json()

    preco = client.post(
        "/precos",
        headers=headers,
        json={"id_bebida": bebida["id_bebida"], "valor": -1},
    )
    assert preco.status_code == 422

    avaliacao = client.post(
        "/avaliacoes",
        headers=headers,
        json={"id_bebida": bebida["id_bebida"], "nota": 6},
    )
    assert avaliacao.status_code == 422


def test_xss_escapado_na_web():
    resposta = client.get("/web/login")
    assert resposta.status_code == 200
    web = client.post(
        "/web/registrar",
        data={
            "nome": "<script>alert(1)</script>",
            "nome_usuario": f"xss_{uuid.uuid4().hex[:12]}",
            "email": f"xss-{uuid.uuid4().hex}@example.com",
            "senha": "Senha@123",
            "data_nascimento": "1990-01-01",
            "aceitou_privacidade": "true",
            "aceitou_termos": "true",
        },
        follow_redirects=False,
    )
    assert web.status_code == 303
    client.cookies.update(web.cookies)

    home = client.get("/web/")
    assert "<script>alert(1)</script>" not in home.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in home.text


def test_requisicao_muito_grande_bloqueada():
    resposta = client.post(
        "/auth/login",
        json={"email": "a" * 1000 + "@example.com", "senha": "Senha@123"},
    )
    assert resposta.status_code == 413


def test_cadastro_rejeita_senha_fraca_e_email_invalido():
    base = {
        "nome": "Usuario QA",
        "nome_usuario": f"validacao_{uuid.uuid4().hex[:12]}",
        "data_nascimento": "1990-01-01",
        "aceitou_privacidade": True,
        "aceitou_termos": True,
        "marketing_consentimento": False,
    }

    senha_fraca = client.post(
        "/auth/registrar",
        json={
            **base,
            "email": f"senha-fraca-{uuid.uuid4().hex}@example.com",
            "senha": "12345678",
        },
    )
    assert senha_fraca.status_code == 422

    email_invalido = client.post(
        "/auth/registrar",
        json={
            **base,
            "nome_usuario": f"email_{uuid.uuid4().hex[:12]}",
            "email": "teste@example.com'; DROP TABLE usuario; --",
            "senha": "Senha@123",
        },
    )
    assert email_invalido.status_code == 422


def test_web_cadastro_rejeita_email_invalido_e_senha_fraca():
    resposta_email = client.post(
        "/web/registrar",
        data={
            "nome": "Usuario Web",
            "nome_usuario": f"web_email_{uuid.uuid4().hex[:12]}",
            "email": "teste@example.com'; DROP TABLE usuario; --",
            "senha": "Senha@123",
            "data_nascimento": "1990-01-01",
            "aceitou_privacidade": "true",
            "aceitou_termos": "true",
        },
    )
    assert resposta_email.status_code == 200
    assert "Informe um e-mail válido" in resposta_email.text

    resposta_senha = client.post(
        "/web/registrar",
        data={
            "nome": "Usuario Web",
            "nome_usuario": f"web_senha_{uuid.uuid4().hex[:12]}",
            "email": f"web-senha-{uuid.uuid4().hex}@example.com",
            "senha": "12345678",
            "data_nascimento": "1990-01-01",
            "aceitou_privacidade": "true",
            "aceitou_termos": "true",
        },
    )
    assert resposta_senha.status_code == 200
    assert "letra maiúscula" in resposta_senha.text


def test_logger_json_mascara_dados_sensiveis():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="bebidas_scan.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="login email=usuario@example.com token=abc123 senha=Segredo@123",
        args=(),
        exc_info=None,
    )
    record.access_token = "token-real"
    record.password = "senha-real"
    record.identity = "usuario@example.com"

    saida = formatter.format(record)

    assert "token-real" not in saida
    assert "senha-real" not in saida
    assert "usuario@example.com" not in saida
    assert "***MASKED***" in saida


def test_qa_web_fluxo_botao_por_botao_cadastro_bebida_favorito_avaliacao_privacidade_logout():
    local = TestClient(app)
    email = f"qa-web-{uuid.uuid4().hex}@example.com"
    nome_usuario = f"qaweb_{uuid.uuid4().hex[:12]}"

    login_page = local.get("/web/login")
    assert login_page.status_code == 200
    for trecho in [
        'name="identificador"',
        'name="senha"',
        'type="submit">Entrar',
        'href="/web/registrar"',
    ]:
        assert trecho in login_page.text

    registrar_page = local.get("/web/registrar")
    assert registrar_page.status_code == 200
    for campo in [
        'name="nome"',
        'name="nome_usuario"',
        'name="email"',
        'name="senha"',
        'name="data_nascimento"',
        'name="aceitou_privacidade"',
        'name="aceitou_termos"',
        'name="marketing_consentimento"',
    ]:
        assert campo in registrar_page.text

    cadastro = local.post(
        "/web/registrar",
        data={
            "nome": "Usuario QA Web",
            "nome_usuario": nome_usuario,
            "email": email,
            "senha": "Senha@123",
            "data_nascimento": "1990-01-01",
            "aceitou_privacidade": "true",
            "aceitou_termos": "true",
            "marketing_consentimento": "true",
        },
        follow_redirects=False,
    )
    assert cadastro.status_code == 303
    assert "web_access_token" in cadastro.cookies
    assert "web_refresh_token" in cadastro.cookies
    local.cookies.update(cadastro.cookies)

    home = local.get("/web/")
    assert home.status_code == 200
    for trecho in ["Buscar bebida", "Escanear código", "Cadastrar bebida", "Favoritos", "Privacidade"]:
        assert trecho in home.text

    scanner = local.get("/web/scanner")
    assert scanner.status_code == 200
    scanner_csrf = csrf_from(scanner.text)
    for trecho in ["Abrir câmera", "Parar câmera", 'name="codigo"', "Buscar código"]:
        assert trecho in scanner.text
    busca_codigo = local.post(
        "/web/buscar-codigo",
        data={"codigo": "7891234567890", "csrf_token": scanner_csrf},
        follow_redirects=False,
    )
    assert busca_codigo.status_code == 303
    assert "/web/bebidas/nova?codigo_barras=7891234567890" in busca_codigo.headers["location"]

    nova = local.get("/web/bebidas/nova?codigo_barras=7891234567890")
    assert nova.status_code == 200
    nova_csrf = csrf_from(nova.text)
    for campo in [
        'name="nome"',
        'name="marca"',
        'name="tipo"',
        'name="codigo_barras"',
        'name="teor_alcoolico"',
        'name="ingredientes"',
        'name="imagem_url"',
        'name="volume_ml"',
        'name="classificacao"',
        'name="madeira"',
        'name="tempo_envelhecimento_meses"',
        'name="cidade_origem"',
        'name="estado_origem"',
        'name="regiao_origem"',
        'name="alambique"',
        'name="produtor"',
        'name="lote"',
        "Salvar bebida",
        "Cancelar",
    ]:
        assert campo in nova.text

    criar_bebida = local.post(
        "/web/bebidas/nova",
        data={
            "csrf_token": nova_csrf,
            "nome": "Cachaça QA",
            "marca": "Marca QA",
            "tipo": "cachaca",
            "codigo_barras": "7891234567890",
            "teor_alcoolico": "40",
            "ingredientes": "Cana-de-açúcar",
            "imagem_url": "",
            "volume_ml": "700",
            "classificacao": "Prata",
            "madeira": "Amburana",
            "tempo_envelhecimento_meses": "12",
            "cidade_origem": "Cascavel",
            "estado_origem": "pr",
            "regiao_origem": "Oeste",
            "alambique": "Alambique QA",
            "produtor": "Produtor QA",
            "lote": "L1",
        },
        follow_redirects=False,
    )
    assert criar_bebida.status_code == 303
    detalhe_url = criar_bebida.headers["location"]
    assert detalhe_url.startswith("/web/bebidas/")

    detalhe = local.get(detalhe_url)
    assert detalhe.status_code == 200
    detalhe_csrf = csrf_from(detalhe.text)
    for trecho in ["Favoritar", "Minha avaliação", "Salvar avaliação", "Dados de cachaça"]:
        assert trecho in detalhe.text

    id_bebida = int(detalhe_url.rsplit("/", 1)[1])
    favorito = local.post(
        f"/web/favoritos/{id_bebida}",
        data={"csrf_token": detalhe_csrf},
        follow_redirects=False,
    )
    assert favorito.status_code == 303

    favoritos = local.get("/web/favoritos")
    assert favoritos.status_code == 200
    assert "Cachaça QA" in favoritos.text

    avaliacao = local.post(
        "/web/avaliacoes",
        data={
            "csrf_token": detalhe_csrf,
            "id_bebida": str(id_bebida),
            "nota": "5",
            "comentario": "Muito boa",
            "compraria_novamente": "true",
        },
        follow_redirects=False,
    )
    assert avaliacao.status_code == 303

    minhas = local.get("/web/minhas-avaliacoes")
    assert minhas.status_code == 200
    assert "Muito boa" in minhas.text

    privacidade = local.get("/web/minha-privacidade")
    assert privacidade.status_code == 200
    privacidade_csrf = csrf_from(privacidade.text)
    for campo in ["Exportar meus dados", "Baixar CSV", 'name="email_confirmacao"', 'name="senha_confirmacao"']:
        assert campo in privacidade.text

    csv = local.get("/web/minha-privacidade/exportar?categoria=perfil&categoria=avaliacoes&categoria=favoritos&categoria=bebidas")
    assert csv.status_code == 200
    assert "text/csv" in csv.headers["content-type"]
    assert "Cachaça QA" in csv.text

    logout = local.post("/web/logout", data={"csrf_token": privacidade_csrf}, follow_redirects=False)
    assert logout.status_code == 303
    assert logout.headers["location"] == "/web/login"


def test_qa_admin_paginas_botoes_e_campos_principais():
    local = TestClient(app)
    auth = ("admin_test", "senha_admin_test")

    sem_auth = local.get("/admin/", follow_redirects=False)
    assert sem_auth.status_code == 401

    dashboard = local.get("/admin/", auth=auth)
    assert dashboard.status_code == 200
    for link in ["/admin/usuarios", "/admin/bebidas", "/admin/avaliacoes", "/admin/favoritos", "/admin/precos", "/docs"]:
        assert link in dashboard.text

    usuarios = local.get("/admin/usuarios", auth=auth)
    assert usuarios.status_code == 200
    usuarios_csrf = csrf_from(usuarios.text)
    for campo in [
        'name="nome"',
        'name="nome_usuario"',
        'name="email"',
        'name="senha"',
        'name="confirmou_maioridade"',
        'name="email_verificado"',
        'name="ativo"',
        "Criar usuário",
    ]:
        assert campo in usuarios.text

    nome_usuario = f"adminqa_{uuid.uuid4().hex[:10]}"
    criar_usuario = local.post(
        "/admin/usuarios/criar",
        auth=auth,
        data={
            "csrf_token": usuarios_csrf,
            "nome": "Admin QA User",
            "nome_usuario": nome_usuario,
            "email": f"{nome_usuario}@example.com",
            "senha": "Senha@123",
            "confirmou_maioridade": "true",
            "email_verificado": "true",
            "ativo": "true",
        },
        follow_redirects=False,
    )
    assert criar_usuario.status_code == 303

    bebidas = local.get("/admin/bebidas", auth=auth)
    assert bebidas.status_code == 200
    assert "/admin/bebidas/nova" in bebidas.text
    assert 'name="q"' in bebidas.text

    bebida_nova = local.get("/admin/bebidas/nova", auth=auth)
    assert bebida_nova.status_code == 200
    for campo in [
        'name="nome"',
        'name="marca"',
        'name="tipo"',
        'name="codigo_barras"',
        'name="teor_alcoolico"',
        'name="volume_ml"',
        'name="madeira"',
        'name="estado_origem"',
        "Criar bebida",
    ]:
        assert campo in bebida_nova.text

    for rota, botao in [
        ("/admin/avaliacoes", "Criar avaliação"),
        ("/admin/favoritos", "Criar favorito"),
        ("/admin/precos", "Criar preço"),
    ]:
        pagina = local.get(rota, auth=auth)
        assert pagina.status_code == 200
        assert botao in pagina.text
        assert 'name="id_usuario"' in pagina.text
        assert 'name="id_bebida"' in pagina.text

from html import escape

from fastapi.responses import HTMLResponse

from ..tipos_bebida import bebida_e_cachaca


def txt(value) -> str:
    if value is None:
        return ""
    return escape(str(value))


def sim_nao(value: bool | None) -> str:
    return "Sim" if value else "Não"


def html_response(html: str) -> HTMLResponse:
    response = HTMLResponse(html)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "base-uri 'none'; "
        "frame-ancestors 'none'; "
        "form-action 'self'"
    )
    return response


def layout(title: str, content: str) -> HTMLResponse:
    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} - Admin Bebidas Scan</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7faf8;
      --surface: #ffffff;
      --text: #17211c;
      --muted: #5e6b64;
      --border: #d9e3dd;
      --accent: #1f7a5c;
      --danger: #9f1d1d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    header, nav, main {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; }}
    header {{ padding: 24px 0 12px; }}
    nav ul {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      list-style: none;
      padding: 0;
      margin: 0 0 20px;
    }}
    nav a, button, .button {{
      display: inline-block;
      border: 1px solid var(--accent);
      border-radius: 6px;
      padding: 8px 12px;
      background: var(--accent);
      color: #fff;
      text-decoration: none;
      font: inherit;
      cursor: pointer;
    }}
    button.secondary, .button.secondary {{
      background: #fff;
      color: var(--accent);
    }}
    button.danger {{
      border-color: var(--danger);
      background: var(--danger);
    }}
    section, form.panel {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
    }}
    .number {{ font-size: 2rem; font-weight: 700; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--surface);
    }}
    caption {{
      text-align: left;
      font-weight: 700;
      padding: 8px 0;
    }}
    th, td {{
      border-top: 1px solid var(--border);
      padding: 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{ background: #eef6f2; }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    label {{ display: block; font-weight: 700; margin-top: 12px; }}
    input, textarea, select {{
      width: 100%;
      max-width: 680px;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px;
      font: inherit;
    }}
    input[type="checkbox"] {{
      width: auto;
      max-width: none;
      margin-right: 6px;
    }}
    textarea {{ min-height: 90px; }}
    .muted {{ color: var(--muted); }}
    .error {{ color: var(--danger); font-weight: 700; }}
    @media (max-width: 720px) {{
      table, thead, tbody, th, td, tr {{ display: block; }}
      tr {{ border-top: 1px solid var(--border); padding: 8px 0; }}
      th {{ display: none; }}
      td {{ border-top: 0; padding: 4px 0; }}
      td::before {{ content: attr(data-label) ": "; font-weight: 700; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Admin Bebidas Scan</h1>
    <p class="muted">Painel de controle do backend, usuários, bebidas e atividade.</p>
  </header>
  <nav aria-label="Navegação principal do admin">
    <ul>
      <li><a href="/admin">Dashboard</a></li>
      <li><a href="/admin/usuarios">Usuários</a></li>
      <li><a href="/admin/bebidas">Bebidas</a></li>
      <li><a href="/admin/avaliacoes">Avaliações</a></li>
      <li><a href="/admin/favoritos">Favoritos</a></li>
      <li><a href="/admin/precos">Preços</a></li>
      <li><a href="/docs">API Docs</a></li>
    </ul>
  </nav>
  <main id="conteudo">
    {content}
  </main>
</body>
</html>"""
    return html_response(html)


def metric(label: str, value: int | str) -> str:
    return f"""<article class="card">
  <h3>{escape(label)}</h3>
  <p class="number">{escape(str(value))}</p>
</article>"""


def render_activity_list(atividade: dict[str, list]) -> str:
    items: list[str] = []
    for usuario in atividade["usuarios"]:
        items.append(f"<li>Usuário criado: {txt(usuario.nome)} ({txt(usuario.email)})</li>")
    for bebida in atividade["bebidas"]:
        items.append(f"<li>Bebida cadastrada: {txt(bebida.nome)}</li>")
    for avaliacao in atividade["avaliacoes"]:
        items.append(
            f"<li>Avaliação #{avaliacao.id_avaliacao}: nota {txt(avaliacao.nota)} para bebida #{avaliacao.id_bebida}</li>"
        )
    for preco in atividade["precos"]:
        items.append(f"<li>Preço #{preco.id_preco}: R$ {txt(preco.valor)} para bebida #{preco.id_bebida}</li>")

    if not items:
        return "<p>Nenhuma atividade registrada ainda.</p>"
    return "<ul>" + "".join(items[:20]) + "</ul>"


def render_dashboard(admin: str, metricas: dict[str, int], atividade_html: str) -> HTMLResponse:
    content = f"""<section aria-labelledby="titulo-dashboard">
  <h2 id="titulo-dashboard">Dashboard em tempo real</h2>
  <p>Entrou como <strong>{txt(admin)}</strong>. Esta página atualiza a atividade automaticamente.</p>
  <div class="cards" aria-label="Indicadores principais">
    {metric("Usuários", metricas["total_usuarios"])}
    {metric("Usuários ativos", metricas["usuarios_ativos"])}
    {metric("Bebidas", metricas["total_bebidas"])}
    {metric("Avaliações", metricas["total_avaliacoes"])}
    {metric("Favoritos", metricas["total_favoritos"])}
    {metric("Preços", metricas["total_precos"])}
  </div>
</section>
<section aria-labelledby="titulo-atividade">
  <h2 id="titulo-atividade">Atividade recente</h2>
  <div id="atividade" aria-live="polite">
    {atividade_html}
  </div>
</section>
<script>
async function atualizarAtividade() {{
  const resposta = await fetch('/admin/atividade-fragment', {{cache: 'no-store'}});
  if (resposta.ok) {{
    document.getElementById('atividade').innerHTML = await resposta.text();
  }}
}}
setInterval(atualizarAtividade, 5000);
</script>"""
    return layout("Dashboard", content)


def render_usuarios_page(usuarios, csrf_input_html: str) -> HTMLResponse:
    rows = []
    for usuario in usuarios:
        status_label = "Desativar" if usuario.ativo else "Ativar"
        rows.append(
            f"""<tr>
  <td data-label="ID">{usuario.id_usuario}</td>
  <td data-label="Nome">{txt(usuario.nome)}</td>
  <td data-label="Nome de usuário">{txt(usuario.nome_usuario)}</td>
  <td data-label="E-mail">{txt(usuario.email)}</td>
  <td data-label="Ativo">{sim_nao(usuario.ativo)}</td>
  <td data-label="Maioridade">{sim_nao(usuario.confirmou_maioridade)}</td>
  <td data-label="E-mail verificado">{sim_nao(usuario.email_verificado)}</td>
  <td data-label="Criado em">{txt(usuario.data_criacao)}</td>
  <td data-label="Ações">
    <div class="actions">
      <form method="post" action="/admin/usuarios/{usuario.id_usuario}/status">
        {csrf_input_html}
        <button type="submit" class="secondary">{status_label}</button>
      </form>
      <form method="post" action="/admin/usuarios/{usuario.id_usuario}/verificar-email">
        {csrf_input_html}
        <button type="submit" class="secondary">Verificar e-mail</button>
      </form>
      <form method="post" action="/admin/usuarios/{usuario.id_usuario}/revogar-tokens">
        {csrf_input_html}
        <button type="submit" class="danger">Revogar tokens</button>
      </form>
      <form method="post" action="/admin/usuarios/{usuario.id_usuario}/excluir">
        {csrf_input_html}
        <button type="submit" class="danger">Excluir usuário</button>
      </form>
    </div>
  </td>
</tr>"""
        )

    content = f"""<section>
  <h2>Usuários</h2>
  <form method="post" action="/admin/usuarios/criar" class="panel" aria-labelledby="titulo-criar-usuario">
    {csrf_input_html}
    <h3 id="titulo-criar-usuario">Adicionar usuário</h3>
    <label for="nome">Nome</label>
    <input id="nome" name="nome" required minlength="2" maxlength="150">
    <label for="nome_usuario">Nome de usuário</label>
    <input id="nome_usuario" name="nome_usuario" required minlength="3" maxlength="80">
    <label for="email">E-mail</label>
    <input id="email" name="email" type="email" required maxlength="150">
    <label for="senha">Senha temporária</label>
    <input id="senha" name="senha" type="password" required minlength="8" maxlength="100">
    <label><input name="confirmou_maioridade" type="checkbox" value="true"> Confirmou maioridade</label>
    <label><input name="email_verificado" type="checkbox" value="true"> E-mail verificado</label>
    <label><input name="ativo" type="checkbox" value="true" checked> Usuário ativo</label>
    <button type="submit">Criar usuário</button>
  </form>
  <table>
    <caption>Últimos 200 usuários cadastrados</caption>
    <thead><tr><th>ID</th><th>Nome</th><th>Nome de usuário</th><th>E-mail</th><th>Ativo</th><th>Maioridade</th><th>E-mail verificado</th><th>Criado em</th><th>Ações</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</section>"""
    return layout("Usuários", content)


def _campos_bebida():
    return [
        ("nome", "Nome"),
        ("marca", "Marca"),
        ("tipo", "Tipo"),
        ("codigo_barras", "Código de barras"),
        ("teor_alcoolico", "Teor alcoólico"),
        ("imagem_url", "URL da imagem"),
    ]


def _campos_cachaca():
    return [
        ("volume_ml", "Volume ml"),
        ("classificacao", "Classificação"),
        ("madeira", "Madeira"),
        ("tempo_envelhecimento_meses", "Envelhecimento em meses"),
        ("cidade_origem", "Cidade de origem"),
        ("estado_origem", "Estado de origem"),
        ("regiao_origem", "Região de origem"),
        ("alambique", "Alambique"),
        ("produtor", "Produtor"),
        ("lote", "Lote"),
    ]


def _input_bebida(nome: str, label: str, valor) -> str:
    if nome == "tipo":
        tipo_atual = str(valor or "cachaca")
        opcoes = "".join(
            f'<option value="{codigo}"{" selected" if tipo_atual == codigo else ""}>{texto}</option>'
            for codigo, texto in [
                ("cachaca", "Cachaça"),
                ("aguardente", "Aguardente"),
                ("cerveja", "Cerveja"),
                ("vinho", "Vinho"),
                ("whisky", "Whisky"),
                ("vodka", "Vodka"),
                ("gin", "Gin"),
                ("rum", "Rum"),
                ("licor", "Licor"),
                ("outro", "Outra bebida"),
            ]
        )
        return f'<label for="tipo">Tipo</label><select id="tipo" name="tipo" required>{opcoes}</select>'
    required = " required" if nome in {"nome", "tipo"} else ""
    return f'<label for="{nome}">{label}</label><input id="{nome}" name="{nome}" value="{txt(valor)}"{required}>'


def _script_campos_cachaca() -> str:
    return """<script>
    const tipoSelect = document.getElementById('tipo');
    const camposCachaca = document.getElementById('campos-cachaca');
    function atualizarCamposCachaca() {
      const valor = tipoSelect.value.toLowerCase();
      const mostrar = valor.includes('cachaca') || valor.includes('aguardente');
      camposCachaca.hidden = !mostrar;
      camposCachaca.querySelectorAll('input').forEach((campo) => campo.disabled = !mostrar);
    }
    tipoSelect.addEventListener('change', atualizarCamposCachaca);
    atualizarCamposCachaca();
  </script>"""


def _bebida_rows(bebidas) -> str:
    rows = []
    for bebida in bebidas:
        cachaca = bebida.cachaca if bebida_e_cachaca(bebida.tipo) else None
        rows.append(
            f"""<tr>
  <td data-label="ID">{bebida.id_bebida}</td>
  <td data-label="Nome">{txt(bebida.nome)}</td>
  <td data-label="Marca">{txt(bebida.marca)}</td>
  <td data-label="Tipo">{txt(bebida.tipo)}</td>
  <td data-label="Código">{txt(bebida.codigo_barras)}</td>
  <td data-label="Madeira">{txt(cachaca.madeira if cachaca else None)}</td>
  <td data-label="Origem">{txt(cachaca.cidade_origem if cachaca else None)} {txt(cachaca.estado_origem if cachaca else None)}</td>
  <td data-label="Ações"><a class="button secondary" href="/admin/bebidas/{bebida.id_bebida}/editar">Editar</a></td>
</tr>"""
        )
    return "".join(rows)


def render_bebidas_page(bebidas, q: str) -> HTMLResponse:
    content = f"""<section>
  <h2>Bebidas</h2>
  <p><a class="button" href="/admin/bebidas/nova">Adicionar bebida</a></p>
  <form method="get" action="/admin/bebidas" class="panel">
    <label for="q">Buscar por nome</label>
    <input id="q" name="q" value="{txt(q)}">
    <button type="submit">Buscar</button>
  </form>
  <table>
    <caption>Bebidas cadastradas</caption>
    <thead><tr><th>ID</th><th>Nome</th><th>Marca</th><th>Tipo</th><th>Código</th><th>Madeira</th><th>Origem</th><th>Ações</th></tr></thead>
    <tbody>{_bebida_rows(bebidas)}</tbody>
  </table>
</section>"""
    return layout("Bebidas", content)


def render_nova_bebida_form(csrf_input_html: str) -> HTMLResponse:
    content = f"""<form method="post" action="/admin/bebidas/nova" class="panel">
  {csrf_input_html}
  <h2>Adicionar bebida</h2>
  <h3>Dados gerais</h3>
  {''.join(_input_bebida(nome, label, '') for nome, label in _campos_bebida())}
  <label for="ingredientes">Ingredientes</label>
  <textarea id="ingredientes" name="ingredientes"></textarea>
  <section id="campos-cachaca">
    <h3>Dados de cachaça</h3>
    {''.join(_input_bebida(nome, label, '') for nome, label in _campos_cachaca())}
  </section>
  <button type="submit">Criar bebida</button>
  <a class="button secondary" href="/admin/bebidas">Voltar</a>
  {_script_campos_cachaca()}
</form>"""
    return layout("Adicionar bebida", content)


def render_editar_bebida_form(bebida, csrf_input_html: str) -> HTMLResponse:
    inputs = "\n".join(_input_bebida(nome, label, getattr(bebida, nome)) for nome, label in _campos_bebida())
    cachaca = bebida.cachaca
    inputs_cachaca = "\n".join(
        _input_bebida(nome, label, getattr(cachaca, nome, ""))
        for nome, label in _campos_cachaca()
    )
    content = f"""<form method="post" action="/admin/bebidas/{bebida.id_bebida}/editar" class="panel">
  {csrf_input_html}
  <h2>Editar bebida #{bebida.id_bebida}</h2>
  <h3>Dados gerais</h3>
  {inputs}
  <label for="ingredientes">Ingredientes</label>
  <textarea id="ingredientes" name="ingredientes">{txt(bebida.ingredientes)}</textarea>
  <section id="campos-cachaca">
    <h3>Dados de cachaça</h3>
    {inputs_cachaca}
  </section>
  <button type="submit">Salvar bebida</button>
  <a class="button secondary" href="/admin/bebidas">Voltar</a>
  {_script_campos_cachaca()}
</form>
<section>
  <h2>Zona de cuidado</h2>
  <form method="post" action="/admin/bebidas/{bebida.id_bebida}/excluir">
    {csrf_input_html}
    <p>Excluir uma bebida pode falhar se ela tiver avaliações, favoritos ou preços vinculados.</p>
    <button class="danger" type="submit">Excluir bebida</button>
  </form>
</section>"""
    return layout("Editar bebida", content)


def render_avaliacoes_page(avaliacoes, csrf_input_html: str) -> HTMLResponse:
    rows = []
    for avaliacao in avaliacoes:
        rows.append(
            f"""<tr>
  <td data-label="ID">{avaliacao.id_avaliacao}</td>
  <td data-label="Usuário">{avaliacao.id_usuario}</td>
  <td data-label="Bebida">{avaliacao.id_bebida}</td>
  <td data-label="Nota">{avaliacao.nota}</td>
  <td data-label="Comentário">{txt(avaliacao.comentario)}</td>
  <td data-label="Compraria">{sim_nao(avaliacao.compraria_novamente)}</td>
  <td data-label="Ações">
    <form method="post" action="/admin/avaliacoes/{avaliacao.id_avaliacao}/excluir">
      {csrf_input_html}
      <button class="danger" type="submit">Excluir</button>
    </form>
  </td>
</tr>"""
        )
    content = f"""<section>
  <h2>Avaliações</h2>
  <form method="post" action="/admin/avaliacoes/criar" class="panel" aria-labelledby="titulo-criar-avaliacao">
    {csrf_input_html}
    <h3 id="titulo-criar-avaliacao">Adicionar avaliação</h3>
    <label for="avaliacao-id-usuario">ID do usuário</label>
    <input id="avaliacao-id-usuario" name="id_usuario" type="number" min="1" required>
    <label for="avaliacao-id-bebida">ID da bebida</label>
    <input id="avaliacao-id-bebida" name="id_bebida" type="number" min="1" required>
    <label for="avaliacao-nota">Nota</label>
    <input id="avaliacao-nota" name="nota" type="number" min="1" max="5" required>
    <label for="avaliacao-comentario">Comentário</label>
    <textarea id="avaliacao-comentario" name="comentario"></textarea>
    <label><input name="compraria_novamente" type="checkbox" value="true"> Compraria novamente</label>
    <button type="submit">Criar avaliação</button>
  </form>
  <table>
    <caption>Últimas 200 avaliações</caption>
    <thead><tr><th>ID</th><th>Usuário</th><th>Bebida</th><th>Nota</th><th>Comentário</th><th>Compraria</th><th>Ações</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</section>"""
    return layout("Avaliações", content)


def render_favoritos_page(favoritos, csrf_input_html: str) -> HTMLResponse:
    rows = []
    for favorito in favoritos:
        rows.append(
            f"""<tr>
  <td data-label="ID">{favorito.id_favorito}</td>
  <td data-label="Usuário">{favorito.id_usuario}</td>
  <td data-label="Bebida">{favorito.id_bebida}</td>
  <td data-label="Data">{txt(favorito.data_favorito)}</td>
  <td data-label="Ações">
    <form method="post" action="/admin/favoritos/{favorito.id_favorito}/excluir">
      {csrf_input_html}
      <button class="danger" type="submit">Excluir</button>
    </form>
  </td>
</tr>"""
        )
    content = f"""<section>
  <h2>Favoritos</h2>
  <form method="post" action="/admin/favoritos/criar" class="panel" aria-labelledby="titulo-criar-favorito">
    {csrf_input_html}
    <h3 id="titulo-criar-favorito">Adicionar favorito</h3>
    <label for="favorito-id-usuario">ID do usuário</label>
    <input id="favorito-id-usuario" name="id_usuario" type="number" min="1" required>
    <label for="favorito-id-bebida">ID da bebida</label>
    <input id="favorito-id-bebida" name="id_bebida" type="number" min="1" required>
    <button type="submit">Criar favorito</button>
  </form>
  <table>
    <caption>Últimos 200 favoritos</caption>
    <thead><tr><th>ID</th><th>Usuário</th><th>Bebida</th><th>Data</th><th>Ações</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</section>"""
    return layout("Favoritos", content)


def render_precos_page(precos, csrf_input_html: str) -> HTMLResponse:
    rows = []
    for preco in precos:
        rows.append(
            f"""<tr>
  <td data-label="ID">{preco.id_preco}</td>
  <td data-label="Usuário">{preco.id_usuario}</td>
  <td data-label="Bebida">{preco.id_bebida}</td>
  <td data-label="Valor">R$ {txt(preco.valor)}</td>
  <td data-label="Local">{txt(preco.mercado)} {txt(preco.cidade)} {txt(preco.estado)}</td>
  <td data-label="Data">{txt(preco.data_registro)}</td>
  <td data-label="Ações">
    <form method="post" action="/admin/precos/{preco.id_preco}/excluir">
      {csrf_input_html}
      <button class="danger" type="submit">Excluir</button>
    </form>
  </td>
</tr>"""
        )
    content = f"""<section>
  <h2>Preços</h2>
  <form method="post" action="/admin/precos/criar" class="panel" aria-labelledby="titulo-criar-preco">
    {csrf_input_html}
    <h3 id="titulo-criar-preco">Adicionar preço</h3>
    <label for="preco-id-usuario">ID do usuário</label>
    <input id="preco-id-usuario" name="id_usuario" type="number" min="1" required>
    <label for="preco-id-bebida">ID da bebida</label>
    <input id="preco-id-bebida" name="id_bebida" type="number" min="1" required>
    <label for="preco-valor">Valor</label>
    <input id="preco-valor" name="valor" inputmode="decimal" required>
    <label for="preco-mercado">Mercado</label>
    <input id="preco-mercado" name="mercado" maxlength="150">
    <label for="preco-cidade">Cidade</label>
    <input id="preco-cidade" name="cidade" maxlength="100">
    <label for="preco-estado">Estado</label>
    <input id="preco-estado" name="estado" maxlength="2">
    <button type="submit">Criar preço</button>
  </form>
  <table>
    <caption>Últimos 200 preços registrados</caption>
    <thead><tr><th>ID</th><th>Usuário</th><th>Bebida</th><th>Valor</th><th>Local</th><th>Data</th><th>Ações</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</section>"""
    return layout("Preços", content)


from fastapi.responses import HTMLResponse

from ..tipos_bebida import bebida_e_cachaca
from html import escape


def txt(value) -> str:
    if value is None:
        return ""
    return escape(str(value))


def render_login_form(erro: str = "") -> str:
    erro_html = ""
    ajuda_html = '<p class="muted">Use o nome de usuário ou e-mail criado no cadastro. Não existe senha padrão para usuário comum.</p>'
    if erro:
        erro_html = f'<p class="error" role="alert">{txt(erro)}</p>'
        ajuda_html = '<p class="muted">Se ainda não criou uma conta, use "Criar conta". A senha é a que você definiu no cadastro.</p>'
    return f"""<form method="post" action="/web/login" class="panel">
  <h2>Entrar</h2>
  {erro_html}
  {ajuda_html}
  <label for="identificador">Nome de usuário ou e-mail</label>
  <input id="identificador" name="identificador" autocomplete="username" required minlength="3" maxlength="150">
  <label for="senha">Senha</label>
  <input id="senha" name="senha" type="password" autocomplete="current-password" required>
  <p class="actions"><button type="submit">Entrar</button><a href="/web/registrar">Criar conta</a></p>
</form>"""


def render_registrar_form(erro: str = "") -> str:
    erro_html = f'<p class="error" role="alert">{txt(erro)}</p>' if erro else ""
    return f"""<form method="post" action="/web/registrar" class="panel">
  <h2>Criar conta</h2>
  {erro_html}
  <label for="nome">Nome</label>
  <input id="nome" name="nome" required minlength="2" maxlength="150" autocomplete="name">
  <label for="nome_usuario">Nome de usuário</label>
  <input id="nome_usuario" name="nome_usuario" required minlength="3" maxlength="80" autocomplete="username">
  <label for="email">E-mail</label>
  <input id="email" name="email" type="email" required maxlength="150" autocomplete="email" inputmode="email">
  <label for="senha">Senha</label>
  <input id="senha" name="senha" type="password" required minlength="8" maxlength="100" autocomplete="new-password" pattern="(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{{8,}}">
  <p class="muted">Use pelo menos 8 caracteres, uma letra maiúscula, um número e um caractere especial. Guarde essa senha: ela será necessária para entrar e para confirmar exclusão de conta.</p>
  <label for="data_nascimento">Data de nascimento</label>
  <input id="data_nascimento" name="data_nascimento" type="date" required>
  <label><input name="aceitou_privacidade" type="checkbox" value="true" required> Li e aceito a <a href="/web/privacidade" target="_blank" rel="noopener">Política de Privacidade</a></label>
  <label><input name="aceitou_termos" type="checkbox" value="true" required> Li e aceito os <a href="/web/termos" target="_blank" rel="noopener">Termos de Uso</a></label>
  <label><input name="marketing_consentimento" type="checkbox" value="true"> Aceito receber comunicações e novidades do Bebidas Scan</label>
  <p class="actions"><button type="submit">Criar conta</button><a href="/web/login">Já tenho conta</a></p>
</form>"""


def render_documento_legal(titulo: str, versao: str, texto: str) -> str:
    texto_html = escape(texto).replace("\n", "<br>")
    return f"""<section>
  <h2>{txt(titulo)}</h2>
  <p class="muted">Versão {txt(versao)}</p>
  <p>{texto_html}</p>
</section>"""


def render_lgpd_aceite_form(usuario, erro: str = "") -> str:
    erro_html = f'<p class="error" role="alert">{txt(erro)}</p>' if erro else ""
    data_atual = txt(usuario.data_nascimento or "")
    marketing_checked = " checked" if usuario.marketing_consentimento else ""
    return f"""<form method="post" action="/web/lgpd/aceitar" class="panel">
  <h2>Atualização de privacidade</h2>
  {erro_html}
  <p>Para continuar usando o Bebidas Scan, confirme sua data de nascimento e aceite a versão vigente da Política de Privacidade e dos Termos de Uso.</p>
  <label for="data_nascimento">Data de nascimento</label>
  <input id="data_nascimento" name="data_nascimento" type="date" required value="{data_atual}">
  <label><input name="aceitou_privacidade" type="checkbox" value="true" required> Li e aceito a <a href="/web/privacidade" target="_blank" rel="noopener">Política de Privacidade</a></label>
  <label><input name="aceitou_termos" type="checkbox" value="true" required> Li e aceito os <a href="/web/termos" target="_blank" rel="noopener">Termos de Uso</a></label>
  <label><input name="marketing_consentimento" type="checkbox" value="true"{marketing_checked}> Aceito receber comunicações e novidades do Bebidas Scan</label>
  <p class="actions"><button type="submit">Aceitar e continuar</button></p>
</form>"""


def render_minha_privacidade(usuario, csrf_input_html: str) -> str:
    return f"""<section>
  <h2>Minha privacidade</h2>
  <p>Política aceita: {txt(usuario.privacidade_versao_aceita) or 'pendente'}</p>
  <p>Termos aceitos: {txt(usuario.termos_versao_aceita) or 'pendente'}</p>
  <p>Aceite registrado em: {txt(usuario.lgpd_aceite_em) or 'pendente'}</p>
  <p>Marketing: {'sim' if usuario.marketing_consentimento else 'não'}</p>
</section>
<section>
  <h2>Exportar meus dados</h2>
  <form method="get" action="/web/minha-privacidade/exportar" class="panel">
    <label><input type="checkbox" name="categoria" value="perfil" checked> Perfil</label>
    <label><input type="checkbox" name="categoria" value="avaliacoes" checked> Avaliações</label>
    <label><input type="checkbox" name="categoria" value="favoritos" checked> Favoritos</label>
    <label><input type="checkbox" name="categoria" value="precos" checked> Preços</label>
    <label><input type="checkbox" name="categoria" value="bebidas" checked> Bebidas cadastradas</label>
    <button type="submit">Baixar CSV</button>
  </form>
</section>
<section>
  <h2>Excluir minha conta</h2>
  <form method="post" action="/web/minha-privacidade/anonimizar" class="panel">
    {csrf_input_html}
    <p>Esta ação desativa sua conta, revoga sessões, apaga favoritos, remove comentários de avaliações e anonimiza os vínculos pessoais.</p>
    <label for="email_confirmacao">Confirme seu e-mail</label>
    <input id="email_confirmacao" name="email_confirmacao" type="email" required maxlength="150" autocomplete="email" inputmode="email">
    <label for="senha_confirmacao">Confirme sua senha</label>
    <input id="senha_confirmacao" name="senha_confirmacao" type="password" required autocomplete="current-password">
    <button class="danger" type="submit">Excluir e anonimizar conta</button>
  </form>
</section>"""


def render_minha_privacidade_erro(erro: str) -> str:
    return f"""<section>
  <h2>Minha privacidade</h2>
  <p class="error" role="alert">{txt(erro)}</p>
  <p><a class="button" href="/web/minha-privacidade">Voltar</a></p>
</section>"""


def render_cards_page(titulo: str, cards: str, vazio: str) -> str:
    cards = cards or f'<p class="muted">{txt(vazio)}</p>'
    return f"<section><h2>{txt(titulo)}</h2><div class=\"grid\">{cards}</div></section>"


def render_home(q: str, cards: str, sem_resultados: bool) -> str:
    if sem_resultados:
        cards = '<p class="muted">Nenhuma bebida encontrada. Você pode cadastrar manualmente.</p>'
    return f"""<section class="hero">
  <div>
    <h2>Buscar bebida</h2>
    <form method="get" action="/web/" class="panel" role="search">
      <label for="q">Nome da bebida</label>
      <input id="q" name="q" value="{txt(q)}" minlength="2" maxlength="80">
      <p class="actions">
        <button type="submit">Buscar</button>
        <a class="button secondary" href="/web/scanner">Escanear código</a>
      </p>
    </form>
  </div>
  <aside>
    <h2>Sua adega digital</h2>
    <p>Escaneie códigos, encontre bebidas, salve favoritos e registre suas avaliações.</p>
    <p class="muted">Cachaças e destilados podem ser cadastrados com dados detalhados.</p>
  </aside>
</section>
<section>
  <h2>Resultados</h2>
  <div class="grid">{cards}</div>
</section>"""


def render_minhas_avaliacoes(avaliacoes) -> str:
    rows = ""
    for avaliacao in avaliacoes:
        rows += f"""<article class="card">
  <h3>{txt(avaliacao.bebida.nome if avaliacao.bebida else 'Bebida')}</h3>
  <p>Nota: {avaliacao.nota}</p>
  <p>{txt(avaliacao.comentario)}</p>
  <a href="/web/bebidas/{avaliacao.id_bebida}">Abrir bebida</a>
</article>"""
    return render_cards_page("Minhas avaliações", rows, "Nenhuma avaliação ainda.")



def html_response(html: str) -> HTMLResponse:
    response = HTMLResponse(html)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(self)"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' https: data:; "
        "media-src 'self' blob:; "
        "connect-src 'self'; "
        "base-uri 'none'; "
        "frame-ancestors 'none'; "
        "form-action 'self'"
    )
    return response


def layout(
    title: str,
    content: str,
    usuario=None,
    csrf_input_html: str = "",
) -> HTMLResponse:
    auth_links = (
        f"""<span>{txt(usuario.nome)}</span>
        <form method="post" action="/web/logout" class="logout-form">
          {csrf_input_html}
          <button type="submit" class="secondary">Sair</button>
        </form>"""
        if usuario
        else '<a href="/web/login">Entrar</a><a href="/web/registrar">Criar conta</a>'
    )
    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{txt(title)} - Bebidas Scan</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #130f0d;
      --surface: #211916;
      --surface-2: #2d221d;
      --text: #fbf5ec;
      --muted: #cdbfaa;
      --border: #4b392f;
      --accent: #d79a3b;
      --accent-2: #2f8d6a;
      --wine: #7a2434;
      --danger: #d16060;
      --shadow: 0 18px 55px rgba(0, 0, 0, .34);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background:
        radial-gradient(circle at 18% 0%, rgba(215, 154, 59, .20), transparent 34rem),
        radial-gradient(circle at 85% 10%, rgba(122, 36, 52, .34), transparent 30rem),
        linear-gradient(180deg, #130f0d 0%, #1b1412 48%, #120f0e 100%);
      color: var(--text);
      line-height: 1.5;
      min-height: 100vh;
    }}
    header, nav, main {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
    }}
    header {{
      padding: 24px 0 12px;
      display: flex;
      justify-content: space-between;
      align-items: start;
      gap: 16px;
    }}
    header h1 {{
      margin: 0;
      font-size: clamp(2rem, 5vw, 4.25rem);
      line-height: .95;
      letter-spacing: 0;
    }}
    header p {{ margin: 10px 0 0; }}
    nav ul {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      list-style: none;
      padding: 0;
      margin: 0 0 22px;
    }}
    a, button, .button {{
      color: var(--accent);
      font: inherit;
    }}
    button, .button {{
      display: inline-block;
      border: 1px solid var(--accent);
      border-radius: 6px;
      padding: 10px 14px;
      background: var(--accent);
      color: #19100b;
      text-decoration: none;
      cursor: pointer;
      font-weight: 700;
      box-shadow: 0 8px 22px rgba(215, 154, 59, .18);
      transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    }}
    button:hover, .button:hover {{
      transform: translateY(-1px);
      box-shadow: 0 12px 28px rgba(215, 154, 59, .24);
    }}
    .secondary {{
      background: rgba(255, 255, 255, .06);
      color: var(--accent);
      border-color: rgba(215, 154, 59, .44);
      box-shadow: none;
    }}
    .danger {{
      border-color: var(--danger);
      background: var(--danger);
      color: white;
    }}
    section, form.panel, article.card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
      box-shadow: var(--shadow);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 14px;
    }}
    label {{ display: block; font-weight: 700; margin-top: 12px; }}
    input, textarea, select {{
      width: 100%;
      max-width: 680px;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 11px;
      font: inherit;
      background: #130f0d;
      color: var(--text);
    }}
    input:focus, textarea:focus, select:focus {{
      outline: 2px solid rgba(215, 154, 59, .58);
      outline-offset: 2px;
    }}
    input[type="checkbox"] {{ width: auto; margin-right: 6px; }}
    textarea {{ min-height: 90px; }}
    .muted {{ color: var(--muted); }}
    .error {{ color: var(--danger); font-weight: 700; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    .logout-form {{ display: inline; margin: 0; }}
    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(320px, .95fr);
      gap: 16px;
      align-items: stretch;
      min-height: 520px;
    }}
    .hero > div:first-child, .hero > aside {{
      min-height: 100%;
    }}
    .hero form.panel {{
      background: rgba(33, 25, 22, .88);
      backdrop-filter: blur(12px);
    }}
    .hero aside {{
      position: relative;
      overflow: hidden;
      min-height: 480px;
      padding: 0;
      background:
        linear-gradient(180deg, rgba(19, 15, 13, .04), rgba(19, 15, 13, .92)),
        url("https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=1200&q=80") center / cover;
      isolation: isolate;
    }}
    .hero aside h2, .hero aside p {{
      position: relative;
      z-index: 2;
      margin-left: 18px;
      margin-right: 18px;
    }}
    .hero aside h2 {{
      margin-top: 300px;
      font-size: clamp(1.8rem, 3vw, 2.8rem);
      line-height: 1;
    }}
    .hero aside::before {{
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(100deg, transparent 0 34%, rgba(255,255,255,.16) 46%, transparent 58%),
        radial-gradient(circle at 28% 24%, rgba(215,154,59,.30), transparent 20rem);
      transform: translateX(-80%);
      animation: ambientSweep 8s ease-in-out infinite;
      z-index: 1;
    }}
    .hero aside::after {{
      content: "";
      position: absolute;
      right: 18px;
      top: 18px;
      width: 110px;
      height: 70px;
      background:
        linear-gradient(to top, rgba(215,154,59,.95) 32%, transparent 32% 100%) 0 100% / 12px 100% no-repeat,
        linear-gradient(to top, rgba(47,141,106,.95) 62%, transparent 62% 100%) 24px 100% / 12px 100% no-repeat,
        linear-gradient(to top, rgba(122,36,52,.95) 44%, transparent 44% 100%) 48px 100% / 12px 100% no-repeat,
        linear-gradient(to top, rgba(215,154,59,.95) 82%, transparent 82% 100%) 72px 100% / 12px 100% no-repeat,
        linear-gradient(to top, rgba(47,141,106,.95) 54%, transparent 54% 100%) 96px 100% / 12px 100% no-repeat;
      filter: drop-shadow(0 0 14px rgba(215,154,59,.34));
      animation: equalizer 1.1s ease-in-out infinite alternate;
      z-index: 2;
    }}
    @keyframes ambientSweep {{
      0%, 100% {{ transform: translateX(-78%); opacity: .28; }}
      50% {{ transform: translateX(72%); opacity: .55; }}
    }}
    @keyframes equalizer {{
      0% {{ transform: scaleY(.72); opacity: .72; }}
      100% {{ transform: scaleY(1); opacity: 1; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        animation-duration: .001ms !important;
        animation-iteration-count: 1 !important;
        transition: none !important;
      }}
    }}
    .camera-box {{
      min-height: 280px;
      background: #050706;
      color: white;
      border-radius: 8px;
      overflow: hidden;
      display: grid;
      place-items: center;
    }}
    video {{ width: 100%; height: 100%; object-fit: cover; }}
    img.product {{
      max-width: 100%;
      max-height: 260px;
      object-fit: contain;
      background: rgba(255,255,255,.06);
      border-radius: 8px;
    }}
    @media (max-width: 760px) {{
      header, .hero {{ display: block; }}
      header .actions {{ margin-top: 8px; }}
      .hero {{ min-height: auto; }}
      .hero aside {{ min-height: 360px; }}
      .hero aside h2 {{ margin-top: 190px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Bebidas Scan</h1>
      <p class="muted">Descubra, cadastre e avalie bebidas com facilidade.</p>
    </div>
    <div class="actions" aria-label="Conta">{auth_links}</div>
  </header>
  <nav aria-label="Navegação principal">
    <ul>
      <li><a class="button secondary" href="/web">Início</a></li>
      <li><a class="button secondary" href="/web/scanner">Scanner</a></li>
      <li><a class="button secondary" href="/web/bebidas/nova">Cadastrar bebida</a></li>
      <li><a class="button secondary" href="/web/favoritos">Favoritos</a></li>
      <li><a class="button secondary" href="/web/minhas-avaliacoes">Avaliações</a></li>
      <li><a class="button secondary" href="/web/minha-privacidade">Privacidade</a></li>
    </ul>
  </nav>
  <main id="conteudo">{content}</main>
</body>
</html>"""
    return html_response(html)




def render_bebida_card(bebida) -> str:
    imagem = (
        f'<img class="product" src="{txt(bebida.imagem_url)}" alt="Imagem da bebida {txt(bebida.nome)}">'
        if bebida.imagem_url
        else ""
    )
    return f"""<article class="card">
  {imagem}
  <h3>{txt(bebida.nome)}</h3>
  <p>{txt(bebida.marca) or 'Marca não informada'}</p>
  <p class="muted">{txt(bebida.tipo)}</p>
  <a class="button" href="/web/bebidas/{bebida.id_bebida}">Abrir</a>
</article>"""


def render_bebida_form(bebida, codigo_barras: str, csrf_input_html: str, erro: str = "") -> str:
    cachaca = bebida.cachaca if bebida and bebida_e_cachaca(bebida.tipo) else None
    tipo_atual = bebida.tipo if bebida else "cachaca"
    opcoes_tipo = "".join(
        f'<option value="{valor}"{" selected" if tipo_atual == valor else ""}>{label}</option>'
        for valor, label in [
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
    erro_html = f'<p class="error" role="alert">{txt(erro)}</p>' if erro else ""
    return f"""<form method="post" action="/web/bebidas/nova" class="panel">
  {csrf_input_html}
  <h2>Cadastrar bebida</h2>
  {erro_html}
  <label for="nome">Nome</label>
  <input id="nome" name="nome" required maxlength="200" value="{txt(bebida.nome if bebida else '')}">
  <label for="marca">Marca</label>
  <input id="marca" name="marca" maxlength="150" value="{txt(bebida.marca if bebida else '')}">
  <label for="tipo">Tipo</label>
  <select id="tipo" name="tipo" required>{opcoes_tipo}</select>
  <label for="codigo_barras">Código de barras</label>
  <input id="codigo_barras" name="codigo_barras" maxlength="80" value="{txt(bebida.codigo_barras if bebida else codigo_barras)}">
  <label for="teor_alcoolico">Teor alcoólico (%)</label>
  <input id="teor_alcoolico" name="teor_alcoolico" inputmode="decimal" value="{txt(bebida.teor_alcoolico if bebida else '')}">
  <label for="ingredientes">Ingredientes</label>
  <textarea id="ingredientes" name="ingredientes">{txt(bebida.ingredientes if bebida else '')}</textarea>
  <label for="imagem_url">URL da imagem</label>
  <input id="imagem_url" name="imagem_url" value="{txt(bebida.imagem_url if bebida else '')}">
  <section id="campos-cachaca">
    <h3>Dados de cachaça</h3>
    <label for="volume_ml">Volume ml</label>
    <input id="volume_ml" name="volume_ml" inputmode="numeric" value="{txt(cachaca.volume_ml if cachaca else '')}">
    <label for="classificacao">Classificação</label>
    <input id="classificacao" name="classificacao" value="{txt(cachaca.classificacao if cachaca else '')}">
    <label for="madeira">Madeira</label>
    <input id="madeira" name="madeira" value="{txt(cachaca.madeira if cachaca else '')}">
    <label for="tempo_envelhecimento_meses">Envelhecimento em meses</label>
    <input id="tempo_envelhecimento_meses" name="tempo_envelhecimento_meses" inputmode="numeric" value="{txt(cachaca.tempo_envelhecimento_meses if cachaca else '')}">
    <label for="cidade_origem">Cidade de origem</label>
    <input id="cidade_origem" name="cidade_origem" value="{txt(cachaca.cidade_origem if cachaca else '')}">
    <label for="estado_origem">Estado UF</label>
    <input id="estado_origem" name="estado_origem" maxlength="2" value="{txt(cachaca.estado_origem if cachaca else '')}">
    <label for="regiao_origem">Região de origem</label>
    <input id="regiao_origem" name="regiao_origem" value="{txt(cachaca.regiao_origem if cachaca else '')}">
    <label for="alambique">Alambique</label>
    <input id="alambique" name="alambique" value="{txt(cachaca.alambique if cachaca else '')}">
    <label for="produtor">Produtor</label>
    <input id="produtor" name="produtor" value="{txt(cachaca.produtor if cachaca else '')}">
    <label for="lote">Lote</label>
    <input id="lote" name="lote" value="{txt(cachaca.lote if cachaca else '')}">
  </section>
  <p class="actions"><button type="submit">Salvar bebida</button><a class="button secondary" href="/web">Cancelar</a></p>
  <script>
    const tipoSelect = document.getElementById('tipo');
    const camposCachaca = document.getElementById('campos-cachaca');
    function atualizarCamposCachaca() {{
      const valor = tipoSelect.value.toLowerCase();
      const mostrar = valor.includes('cachaca') || valor.includes('aguardente');
      camposCachaca.hidden = !mostrar;
      camposCachaca.querySelectorAll('input').forEach((campo) => campo.disabled = !mostrar);
    }}
    tipoSelect.addEventListener('change', atualizarCamposCachaca);
    atualizarCamposCachaca();
  </script>
</form>"""


def render_bebida_detalhe(bebida, csrf_input_html: str) -> str:
    cachaca = bebida.cachaca if bebida_e_cachaca(bebida.tipo) else None
    imagem = (
        f'<img class="product" src="{txt(bebida.imagem_url)}" alt="Imagem da bebida {txt(bebida.nome)}">'
        if bebida.imagem_url
        else ""
    )
    favorito_form = f"""<form method="post" action="/web/favoritos/{bebida.id_bebida}">
  {csrf_input_html}
  <button type="submit">Favoritar</button>
</form>"""
    avaliacao_form = f"""<form method="post" action="/web/avaliacoes" class="panel">
  {csrf_input_html}
  <input type="hidden" name="id_bebida" value="{bebida.id_bebida}">
  <h3>Minha avaliação</h3>
  <label for="nota">Nota</label>
  <select id="nota" name="nota">
    <option value="5">5 - Excelente</option>
    <option value="4">4 - Boa</option>
    <option value="3">3 - Regular</option>
    <option value="2">2 - Ruim</option>
    <option value="1">1 - Muito ruim</option>
  </select>
  <label for="comentario">Comentário</label>
  <textarea id="comentario" name="comentario"></textarea>
  <label><input type="checkbox" name="compraria_novamente" value="true"> Compraria novamente</label>
  <button type="submit">Salvar avaliação</button>
</form>"""

    cachaca_html = ""
    if cachaca:
        cachaca_html = f"""<section>
  <h2>Dados de cachaça</h2>
  <p>Volume: {txt(cachaca.volume_ml)} ml</p>
  <p>Classificação: {txt(cachaca.classificacao) or 'Não informada'}</p>
  <p>Madeira: {txt(cachaca.madeira) or 'Não informada'}</p>
  <p>Envelhecimento: {txt(cachaca.tempo_envelhecimento_meses)} meses</p>
  <p>Origem: {txt(cachaca.cidade_origem)} {txt(cachaca.estado_origem)}</p>
  <p>Alambique: {txt(cachaca.alambique) or 'Não informado'}</p>
  <p>Produtor: {txt(cachaca.produtor) or 'Não informado'}</p>
  <p>Lote: {txt(cachaca.lote) or 'Não informado'}</p>
</section>"""

    dados_open_food_facts = [
        ("Nutri-Score", bebida.nutri_score.upper() if bebida.nutri_score else None),
        ("Grupo NOVA", bebida.nova_grupo),
        ("Eco-Score", bebida.eco_score.upper() if bebida.eco_score else None),
        ("Alérgenos", bebida.alergenos),
        ("Categorias", bebida.categorias),
        ("Quantidade", bebida.quantidade),
        ("Embalagem", bebida.embalagem),
        ("Países", bebida.paises),
    ]
    dados_open_food_facts_html = "".join(
        f"<p>{rotulo}: {txt(valor)}</p>"
        for rotulo, valor in dados_open_food_facts
        if valor not in (None, "")
    )
    open_food_facts_html = (
        f"""<section>
  <h2>Dados do Open Food Facts</h2>
  {dados_open_food_facts_html}
</section>"""
        if dados_open_food_facts_html
        else ""
    )

    return f"""<section>
  <div class="hero">
    <div>
      <h2>{txt(bebida.nome)}</h2>
      <p>Marca: {txt(bebida.marca) or 'Não informada'}</p>
      <p>Tipo: {txt(bebida.tipo)}</p>
      <p>Código: {txt(bebida.codigo_barras) or 'Não informado'}</p>
      <p>Teor alcoólico: {txt(bebida.teor_alcoolico)}%</p>
      <p>Ingredientes: {txt(bebida.ingredientes) or 'Não informado'}</p>
      <div class="actions">{favorito_form}</div>
    </div>
    <div>{imagem}</div>
  </div>
</section>
{open_food_facts_html}
{cachaca_html}
{avaliacao_form}"""




def render_scanner(csrf_input_html: str) -> str:
    content = """<section>
  <h2>Escanear código de barras</h2>
  <p class="muted">Aponte a câmera para o código de barras ou digite o código manualmente.</p>
  <div class="camera-box">
    <video id="video" autoplay playsinline muted hidden></video>
    <p id="camera-status">Câmera ainda não iniciada.</p>
  </div>
  <p class="actions">
    <button type="button" id="start-camera">Abrir câmera</button>
    <button type="button" id="stop-camera" class="secondary">Parar câmera</button>
  </p>
  <form method="post" action="/web/buscar-codigo" class="panel">
    __CSRF_INPUT__
    <label for="codigo">Código de barras</label>
    <input id="codigo" name="codigo" inputmode="numeric" minlength="6" maxlength="80" required>
    <button type="submit">Buscar código</button>
  </form>
</section>
<script>
const video = document.getElementById('video');
const statusEl = document.getElementById('camera-status');
const codigoInput = document.getElementById('codigo');
const startButton = document.getElementById('start-camera');
const stopButton = document.getElementById('stop-camera');
let stream = null;
let detector = null;
let lendo = false;

function navegadorPermiteCamera() {
  return Boolean(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
}

function explicarErroCamera(error) {
  if (!window.isSecureContext) {
    return 'A câmera do navegador só funciona em HTTPS ou localhost. Acesse por https:// no domínio ou use http://localhost:8000 neste computador.';
  }
  if (!navegadorPermiteCamera()) {
    return 'Este navegador não liberou acesso à câmera. Use Chrome/Edge atualizado ou digite o código manualmente.';
  }
  if (error && (error.name === 'NotAllowedError' || error.name === 'SecurityError')) {
    return 'Permissão da câmera negada. Libere a câmera nas permissões do site e tente novamente.';
  }
  if (error && (error.name === 'NotFoundError' || error.name === 'OverconstrainedError')) {
    return 'Nenhuma câmera compatível foi encontrada. Tente outra câmera ou digite o código manualmente.';
  }
  if (error && error.name === 'NotReadableError') {
    return 'A câmera está em uso por outro aplicativo. Feche outros apps e tente novamente.';
  }
  return 'Não foi possível abrir a câmera. Verifique a permissão do navegador ou digite o código manualmente.';
}

async function abrirStreamCamera() {
  try {
    return await navigator.mediaDevices.getUserMedia({
      video: {facingMode: {ideal: 'environment'}},
      audio: false
    });
  } catch (error) {
    if (error && (error.name === 'OverconstrainedError' || error.name === 'NotFoundError')) {
      return await navigator.mediaDevices.getUserMedia({video: true, audio: false});
    }
    throw error;
  }
}

async function abrirCamera() {
  pararCamera();
  if (!window.isSecureContext || !navegadorPermiteCamera()) {
    statusEl.textContent = explicarErroCamera();
    return;
  }
  if (!('BarcodeDetector' in window)) {
    statusEl.textContent = 'Este navegador abre câmera, mas não tem leitor nativo de código de barras. Use Chrome/Edge atualizado ou digite o código manualmente.';
    return;
  }
  try {
    startButton.disabled = true;
    statusEl.textContent = 'Solicitando permissão da câmera...';
    detector = new BarcodeDetector({formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128']});
    stream = await abrirStreamCamera();
    video.srcObject = stream;
    video.hidden = false;
    await video.play();
    statusEl.textContent = 'Aponte para o código de barras.';
    lendo = true;
    requestAnimationFrame(loopLeitura);
  } catch (error) {
    pararCamera();
    statusEl.textContent = explicarErroCamera(error);
  } finally {
    startButton.disabled = false;
  }
}

async function loopLeitura() {
  if (!lendo || !detector || video.readyState < 2) {
    if (lendo) requestAnimationFrame(loopLeitura);
    return;
  }
  try {
    const codigos = await detector.detect(video);
    if (codigos.length > 0 && codigos[0].rawValue) {
      codigoInput.value = codigos[0].rawValue;
      statusEl.textContent = 'Código detectado: ' + codigos[0].rawValue;
      pararCamera();
      codigoInput.form.requestSubmit();
      return;
    }
  } catch (_) {}
  requestAnimationFrame(loopLeitura);
}

function pararCamera() {
  lendo = false;
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }
  video.pause();
  video.srcObject = null;
  video.hidden = true;
}

startButton.addEventListener('click', abrirCamera);
stopButton.addEventListener('click', pararCamera);
window.addEventListener('pagehide', pararCamera);
</script>"""
    return content.replace("__CSRF_INPUT__", csrf_input_html)

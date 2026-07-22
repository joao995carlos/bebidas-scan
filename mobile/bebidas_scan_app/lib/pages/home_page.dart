import 'dart:async';

import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/token_service.dart';
import 'profile_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final api = ApiService();
  final tokenService = TokenService();
  final pesquisaController = TextEditingController();
  Timer? sugestaoTimer;
  bool pesquisando = false;
  bool buscandoSugestoes = false;
  bool carregandoFavoritos = false;
  bool pesquisaExecutada = false;
  bool convidado = true;
  int abaAtual = 0;
  List<dynamic> resultados = const [];
  List<dynamic> sugestoes = const [];
  List<dynamic> favoritos = const [];
  final List<String> pesquisasRecentes = [];
  String termoSugestoes = '';

  @override
  void initState() {
    super.initState();
    pesquisaController.addListener(agendarSugestoes);
    _carregarEstadoSessao();
  }

  @override
  void dispose() {
    sugestaoTimer?.cancel();
    pesquisaController.removeListener(agendarSugestoes);
    pesquisaController.dispose();
    super.dispose();
  }

  Future<void> _carregarEstadoSessao() async {
    final token = await tokenService.lerAccessToken();
    if (!mounted) return;
    setState(() => convidado = token == null);

    if (token != null) {
      carregarFavoritos();
      try {
        final status = await api.statusLgpd();
        if (!mounted) return;
        if (status.data['pendente'] == true) {
          Navigator.pushReplacementNamed(context, '/lgpd-aceitar');
        }
      } catch (_) {}
    }
  }

  Future<void> carregarFavoritos() async {
    if (convidado || carregandoFavoritos) return;

    setState(() => carregandoFavoritos = true);
    try {
      final resposta = await api.listarFavoritos();
      if (!mounted) return;
      setState(() => favoritos = resposta.data as List<dynamic>);
    } catch (_) {
      if (!mounted) return;
      setState(() => favoritos = const []);
    } finally {
      if (mounted) setState(() => carregandoFavoritos = false);
    }
  }

  Future<void> pesquisar() async {
    final termo = pesquisaController.text.trim();
    if (termo.isEmpty) return;

    sugestaoTimer?.cancel();
    setState(() {
      pesquisando = true;
      sugestoes = const [];
      termoSugestoes = termo;
    });

    try {
      final resposta = await api.buscarBebidaPorNome(termo);
      registrarPesquisaRecente(termo);
      setState(() {
        resultados = resposta.data as List<dynamic>;
        pesquisaExecutada = true;
      });
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Não foi possível pesquisar bebidas.')),
      );
    } finally {
      if (mounted) setState(() => pesquisando = false);
    }
  }

  void agendarSugestoes() {
    final termo = pesquisaController.text.trim();
    sugestaoTimer?.cancel();

    if (termo.length < 2) {
      if (sugestoes.isNotEmpty || buscandoSugestoes) {
        setState(() {
          sugestoes = const [];
          buscandoSugestoes = false;
          termoSugestoes = termo;
        });
      }
      return;
    }

    sugestaoTimer = Timer(const Duration(milliseconds: 450), () {
      carregarSugestoes(termo);
    });
  }

  Future<void> carregarSugestoes(String termo) async {
    if (!mounted) return;
    if (termo == termoSugestoes && sugestoes.isNotEmpty) return;

    setState(() {
      buscandoSugestoes = true;
      termoSugestoes = termo;
    });

    try {
      final resposta = await api.buscarBebidaPorNome(termo);
      if (!mounted || pesquisaController.text.trim() != termo) return;
      setState(() {
        sugestoes = (resposta.data as List<dynamic>).take(5).toList();
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => sugestoes = const []);
    } finally {
      if (mounted && pesquisaController.text.trim() == termo) {
        setState(() => buscandoSugestoes = false);
      }
    }
  }

  void usarSugestao(Map<String, dynamic> bebida) {
    sugestaoTimer?.cancel();
    pesquisaController.text = bebida['nome']?.toString() ?? '';
    setState(() {
      sugestoes = const [];
      resultados = [bebida];
      pesquisaExecutada = true;
      termoSugestoes = pesquisaController.text.trim();
    });
    abrirBebida(bebida);
  }

  void pesquisarTermo(String termo) {
    pesquisaController.text = termo;
    pesquisar();
  }

  void registrarPesquisaRecente(String termo) {
    pesquisasRecentes.remove(termo);
    pesquisasRecentes.insert(0, termo);
    if (pesquisasRecentes.length > 6) {
      pesquisasRecentes.removeRange(6, pesquisasRecentes.length);
    }
  }

  void abrirBebida(Map<String, dynamic> bebida) {
    Navigator.pushNamed(context, '/bebida', arguments: bebida);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          abaAtual == 0
              ? 'Bebidas Scan'
              : (abaAtual == 1 ? 'Favoritos' : 'Perfil'),
        ),
        actions: [
          if (convidado && abaAtual == 0)
            IconButton(
              tooltip: 'Entrar ou criar conta',
              onPressed: () =>
                  Navigator.pushReplacementNamed(context, '/login'),
              icon: const Icon(Icons.login),
            ),
        ],
      ),
      body: SafeArea(
        child: IndexedStack(
          index: abaAtual,
          children: [
            _HomeContent(
              convidado: convidado,
              pesquisando: pesquisando,
              buscandoSugestoes: buscandoSugestoes,
              pesquisaExecutada: pesquisaExecutada,
              resultados: resultados,
              sugestoes: sugestoes,
              pesquisasRecentes: pesquisasRecentes,
              pesquisaController: pesquisaController,
              pesquisar: pesquisar,
              pesquisarTermo: pesquisarTermo,
              usarSugestao: usarSugestao,
              abrirBebida: abrirBebida,
              abrirFavoritos: () => setState(() => abaAtual = 1),
            ),
            _FavoritesContent(
              convidado: convidado,
              carregando: carregandoFavoritos,
              favoritos: favoritos,
              abrirBebida: abrirBebida,
              recarregar: carregarFavoritos,
            ),
            const ProfileContent(),
          ],
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: abaAtual,
        onDestinationSelected: (index) => setState(() => abaAtual = index),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Início',
          ),
          NavigationDestination(
            icon: Icon(Icons.favorite_border),
            selectedIcon: Icon(Icons.favorite),
            label: 'Favoritos',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Perfil',
          ),
        ],
      ),
    );
  }
}

class _HomeContent extends StatelessWidget {
  const _HomeContent({
    required this.convidado,
    required this.pesquisando,
    required this.buscandoSugestoes,
    required this.pesquisaExecutada,
    required this.resultados,
    required this.sugestoes,
    required this.pesquisasRecentes,
    required this.pesquisaController,
    required this.pesquisar,
    required this.pesquisarTermo,
    required this.usarSugestao,
    required this.abrirBebida,
    required this.abrirFavoritos,
  });

  final bool convidado;
  final bool pesquisando;
  final bool buscandoSugestoes;
  final bool pesquisaExecutada;
  final List<dynamic> resultados;
  final List<dynamic> sugestoes;
  final List<String> pesquisasRecentes;
  final TextEditingController pesquisaController;
  final Future<void> Function() pesquisar;
  final void Function(String termo) pesquisarTermo;
  final void Function(Map<String, dynamic> bebida) usarSugestao;
  final void Function(Map<String, dynamic> bebida) abrirBebida;
  final VoidCallback abrirFavoritos;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return ListView(
      keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      children: [
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: colors.primary,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Encontre a bebida certa',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Escaneie, pesquise ou cadastre informações em poucos toques.',
                style: TextStyle(color: Color(0xfffff4e8), height: 1.35),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xfff3b35f),
                    foregroundColor: const Color(0xff241611),
                    minimumSize: const Size.fromHeight(52),
                  ),
                  onPressed: () => Navigator.pushNamed(context, '/scanner'),
                  icon: const Icon(Icons.qr_code_scanner),
                  label: const Text('Escanear bebida'),
                ),
              ),
            ],
          ),
        ),
        if (convidado) ...[
          const SizedBox(height: 12),
          Material(
            color: const Color(0xfffffbf5),
            shape: RoundedRectangleBorder(
              side: const BorderSide(color: Color(0xffead8c6)),
              borderRadius: BorderRadius.circular(8),
            ),
            child: ListTile(
              leading:
                  Icon(Icons.account_circle_outlined, color: colors.tertiary),
              title: const Text('Conta opcional'),
              subtitle: const Text(
                'Entre para avaliar, favoritar e gerenciar sua privacidade.',
              ),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => Navigator.pushReplacementNamed(context, '/login'),
            ),
          ),
        ],
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: _QuickAction(
                icon: Icons.add,
                label: 'Cadastrar',
                color: const Color(0xffb45f2a),
                onTap: () => Navigator.pushNamed(context, '/bebida-form'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _QuickAction(
                icon: Icons.favorite_border,
                label: 'Favoritos',
                color: const Color(0xff7a2434),
                onTap: abrirFavoritos,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _QuickAction(
                icon: Icons.person_outline,
                label: 'Perfil',
                color: const Color(0xff273f73),
                onTap: () => Navigator.pushNamed(context, '/perfil'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),
        const Text(
          'Pesquisar',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 10),
        TextField(
          controller: pesquisaController,
          decoration: InputDecoration(
            labelText: 'Nome, marca ou tipo',
            hintText: 'Ex.: Coca-Cola, água, suco',
            prefixIcon: const Icon(Icons.search),
            suffixIcon: IconButton(
              tooltip: 'Pesquisar',
              onPressed: pesquisando ? null : pesquisar,
              icon: const Icon(Icons.arrow_forward),
            ),
          ),
          textInputAction: TextInputAction.search,
          onSubmitted: (_) => pesquisar(),
        ),
        _SearchSuggestions(
          buscando: buscandoSugestoes,
          sugestoes: sugestoes,
          onTap: usarSugestao,
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final termo in const [
              'coca cola',
              'água',
              'refrigerante',
              'suco',
              'energético',
            ])
              FilterChip(
                label: Text(termo),
                avatar: const Icon(Icons.search, size: 18),
                onSelected: (_) => pesquisarTermo(termo),
              ),
          ],
        ),
        if (pesquisasRecentes.isNotEmpty) ...[
          const SizedBox(height: 16),
          const Text(
            'Recentes',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final termo in pesquisasRecentes)
                ActionChip(
                  avatar: const Icon(Icons.history, size: 18),
                  label: Text(termo),
                  onPressed: () => pesquisarTermo(termo),
                ),
            ],
          ),
        ],
        const SizedBox(height: 16),
        if (pesquisando) const Center(child: CircularProgressIndicator()),
        if (!pesquisando && pesquisaExecutada && resultados.isEmpty)
          _EmptySearchState(
            onCadastrar: () => Navigator.pushNamed(context, '/bebida-form'),
          ),
        if (!pesquisando && resultados.isNotEmpty) ...[
          const Text(
            'Resultados',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 8),
        ],
        for (final item in resultados)
          _BeverageResultCard(
            bebida: Map<String, dynamic>.from(item),
            onTap: () => abrirBebida(Map<String, dynamic>.from(item)),
          ),
      ],
    );
  }
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: const Color(0xfffffbf5),
      shape: RoundedRectangleBorder(
        side: const BorderSide(color: Color(0xffead8c6)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: onTap,
        child: SizedBox(
          height: 78,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: color),
              const SizedBox(height: 6),
              Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FavoritesContent extends StatelessWidget {
  const _FavoritesContent({
    required this.convidado,
    required this.carregando,
    required this.favoritos,
    required this.abrirBebida,
    required this.recarregar,
  });

  final bool convidado;
  final bool carregando;
  final List<dynamic> favoritos;
  final void Function(Map<String, dynamic> bebida) abrirBebida;
  final Future<void> Function() recarregar;

  @override
  Widget build(BuildContext context) {
    if (convidado) {
      return _StatePanel(
        icon: Icons.lock_outline,
        title: 'Entre para ver favoritos',
        text: 'Seus favoritos ficam salvos na sua conta.',
        action: FilledButton.icon(
          onPressed: () => Navigator.pushReplacementNamed(context, '/login'),
          icon: const Icon(Icons.login),
          label: const Text('Entrar'),
        ),
      );
    }

    if (carregando) {
      return const Center(child: CircularProgressIndicator());
    }

    if (favoritos.isEmpty) {
      return _StatePanel(
        icon: Icons.favorite_border,
        title: 'Nada favoritado ainda',
        text: 'Abra uma bebida e toque no coração para guardar aqui.',
        action: OutlinedButton.icon(
          onPressed: recarregar,
          icon: const Icon(Icons.refresh),
          label: const Text('Atualizar'),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: recarregar,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
        children: [
          const Text(
            'Suas bebidas salvas',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 10),
          for (final favorito in favoritos)
            if (favorito is Map && favorito['bebida'] is Map)
              _BeverageResultCard(
                bebida: Map<String, dynamic>.from(favorito['bebida'] as Map),
                onTap: () => abrirBebida(
                  Map<String, dynamic>.from(favorito['bebida'] as Map),
                ),
              ),
        ],
      ),
    );
  }
}

class _StatePanel extends StatelessWidget {
  const _StatePanel({
    required this.icon,
    required this.title,
    required this.text,
    required this.action,
  });

  final IconData icon;
  final String title;
  final String text;
  final Widget action;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 48, color: Theme.of(context).colorScheme.tertiary),
            const SizedBox(height: 12),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            Text(
              text,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 16),
            action,
          ],
        ),
      ),
    );
  }
}

class _BeverageResultCard extends StatelessWidget {
  const _BeverageResultCard({required this.bebida, required this.onTap});

  final Map<String, dynamic> bebida;
  final VoidCallback onTap;

  bool temTexto(String chave) {
    final valor = bebida[chave];
    return valor != null && valor.toString().trim().isNotEmpty;
  }

  Color corTipo() {
    final tipo = (bebida['tipo'] ?? '').toString().toLowerCase();
    if (tipo.contains('agua') || tipo.contains('água')) {
      return const Color(0xff277da1);
    }
    if (tipo.contains('cerveja')) return const Color(0xffb45f2a);
    if (tipo.contains('vinho')) return const Color(0xff7a2434);
    if (tipo.contains('suco')) return const Color(0xff1f7a5c);
    return const Color(0xff273f73);
  }

  @override
  Widget build(BuildContext context) {
    final color = corTipo();
    final imagem = bebida['imagem_url']?.toString();

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: .12),
                  borderRadius: BorderRadius.circular(8),
                ),
                clipBehavior: Clip.antiAlias,
                child: imagem == null || imagem.isEmpty
                    ? Icon(Icons.local_drink_outlined, color: color)
                    : Image.network(
                        imagem,
                        fit: BoxFit.contain,
                        errorBuilder: (_, __, ___) =>
                            Icon(Icons.local_drink_outlined, color: color),
                      ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      bebida['nome'] ?? 'Bebida sem nome',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      bebida['marca'] ??
                          bebida['tipo'] ??
                          'Sem marca informada',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: [
                        _MiniBadge(
                            label: bebida['tipo'] ?? 'bebida', color: color),
                        if (temTexto('paises'))
                          const _MiniBadge(
                            label: 'Brasil',
                            color: Color(0xff1f7a5c),
                          ),
                        if (temTexto('ingredientes'))
                          const _MiniBadge(
                            label: 'Ingredientes',
                            color: Color(0xffb45f2a),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}

class _MiniBadge extends StatelessWidget {
  const _MiniBadge({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .12),
        borderRadius: BorderRadius.circular(99),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}

class _EmptySearchState extends StatelessWidget {
  const _EmptySearchState({required this.onCadastrar});

  final VoidCallback onCadastrar;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xfffffbf5),
        border: Border.all(color: const Color(0xffead8c6)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Icon(
            Icons.search_off,
            size: 42,
            color: Theme.of(context).colorScheme.tertiary,
          ),
          const SizedBox(height: 10),
          const Text(
            'Nenhuma bebida encontrada',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          Text(
            'Tente outro termo ou cadastre a bebida manualmente.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: onCadastrar,
            icon: const Icon(Icons.add),
            label: const Text('Cadastrar bebida'),
          ),
        ],
      ),
    );
  }
}

class _SearchSuggestions extends StatelessWidget {
  const _SearchSuggestions({
    required this.buscando,
    required this.sugestoes,
    required this.onTap,
  });

  final bool buscando;
  final List<dynamic> sugestoes;
  final void Function(Map<String, dynamic> bebida) onTap;

  @override
  Widget build(BuildContext context) {
    if (!buscando && sugestoes.isEmpty) return const SizedBox.shrink();

    final colors = Theme.of(context).colorScheme;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 180),
      margin: const EdgeInsets.only(top: 8),
      decoration: BoxDecoration(
        color: const Color(0xfffffbf5),
        border: Border.all(color: const Color(0xffead8c6)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (buscando)
            LinearProgressIndicator(
              minHeight: 2,
              color: colors.primary,
              backgroundColor: const Color(0xffead8c6),
            ),
          for (final item in sugestoes)
            ListTile(
              dense: true,
              leading: Icon(Icons.search, color: colors.primary),
              title: Text(
                item['nome'] ?? 'Bebida sem nome',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              subtitle: Text(
                item['marca'] ?? item['tipo'] ?? '',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              trailing: const Icon(Icons.north_west, size: 18),
              onTap: () => onTap(Map<String, dynamic>.from(item)),
            ),
        ],
      ),
    );
  }
}

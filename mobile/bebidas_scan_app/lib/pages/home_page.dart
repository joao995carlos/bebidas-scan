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
  bool pesquisaExecutada = false;
  bool convidado = true;
  int abaAtual = 0;
  List<dynamic> resultados = const [];
  List<dynamic> sugestoes = const [];
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
      try {
        final status = await api.statusLgpd();
        if (!mounted) return;
        if (status.data['pendente'] == true) {
          Navigator.pushReplacementNamed(context, '/lgpd-aceitar');
        }
      } catch (_) {}
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

  void abrirBebida(Map<String, dynamic> bebida) {
    Navigator.pushNamed(context, '/bebida', arguments: bebida);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(abaAtual == 0 ? 'Bebidas Scan' : 'Perfil'),
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
              pesquisaController: pesquisaController,
              pesquisar: pesquisar,
              usarSugestao: usarSugestao,
              abrirBebida: abrirBebida,
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
    required this.pesquisaController,
    required this.pesquisar,
    required this.usarSugestao,
    required this.abrirBebida,
  });

  final bool convidado;
  final bool pesquisando;
  final bool buscandoSugestoes;
  final bool pesquisaExecutada;
  final List<dynamic> resultados;
  final List<dynamic> sugestoes;
  final TextEditingController pesquisaController;
  final Future<void> Function() pesquisar;
  final void Function(Map<String, dynamic> bebida) usarSugestao;
  final void Function(Map<String, dynamic> bebida) abrirBebida;

  @override
  Widget build(BuildContext context) {
    return ListView(
      keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'O que você quer fazer?',
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
        ),
        if (convidado) ...[
          const SizedBox(height: 8),
          Text(
            'Você está usando sem conta. Para avaliar e favoritar, entre ou crie uma conta.',
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        ],
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: () => Navigator.pushNamed(context, '/scanner'),
          icon: const Icon(Icons.qr_code_scanner),
          label: const Text('Escanear bebida'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: () => Navigator.pushNamed(context, '/bebida-form'),
          icon: const Icon(Icons.add),
          label: const Text('Cadastrar bebida'),
        ),
        const SizedBox(height: 24),
        TextField(
          controller: pesquisaController,
          decoration: InputDecoration(
            labelText: 'Pesquisar bebida por nome',
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
        const SizedBox(height: 16),
        if (pesquisando) const Center(child: CircularProgressIndicator()),
        if (!pesquisando && pesquisaExecutada && resultados.isEmpty)
          Text(
            'Nenhuma bebida encontrada. Tente outro termo ou cadastre manualmente.',
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        for (final item in resultados)
          ListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(item['nome'] ?? 'Bebida sem nome'),
            subtitle: Text(item['marca'] ?? item['tipo'] ?? ''),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => abrirBebida(Map<String, dynamic>.from(item)),
          ),
      ],
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

import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/token_service.dart';

class BebidaPage extends StatefulWidget {
  const BebidaPage({super.key});

  @override
  State<BebidaPage> createState() => _BebidaPageState();
}

class _BebidaPageState extends State<BebidaPage> {
  final api = ApiService();
  final tokenService = TokenService();
  final comentarioController = TextEditingController();
  int nota = 5;
  bool comprariaNovamente = false;
  bool salvando = false;

  @override
  void dispose() {
    comentarioController.dispose();
    super.dispose();
  }

  Future<void> avaliar(Map<String, dynamic> bebida) async {
    if (!await _exigirConta()) return;

    setState(() => salvando = true);
    try {
      await api.avaliarBebida(
        idBebida: bebida['id_bebida'],
        nota: nota,
        comentario: comentarioController.text,
        comprariaNovamente: comprariaNovamente,
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Avaliação salva com sucesso.')),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Erro ao salvar avaliação.')),
      );
    } finally {
      if (mounted) setState(() => salvando = false);
    }
  }

  Future<void> favoritar(Map<String, dynamic> bebida) async {
    if (!await _exigirConta()) return;

    try {
      await api.favoritar(bebida['id_bebida']);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Bebida adicionada aos favoritos.')),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Não foi possível favoritar.')),
      );
    }
  }

  Future<void> completarDados(Map<String, dynamic> bebida) async {
    if (!await _exigirConta()) return;

    if (!mounted) return;
    Navigator.pushNamed(
      context,
      '/bebida-form',
      arguments: {'bebida': bebida},
    );
  }

  Future<bool> _exigirConta() async {
    final token = await tokenService.lerAccessToken();
    if (token != null) return true;

    if (!mounted) return false;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('Entre ou crie uma conta para usar esse recurso.'),
        action: SnackBarAction(
          label: 'Entrar',
          onPressed: () => Navigator.pushReplacementNamed(context, '/login'),
        ),
      ),
    );
    return false;
  }

  bool tipoEhCachaca(dynamic tipo) {
    final valor = (tipo ?? '').toString().toLowerCase();
    return valor.contains('cachaca') ||
        valor.contains('cachaça') ||
        valor.contains('aguardente');
  }

  bool temTexto(Map<String, dynamic> mapa, String chave) {
    final valor = mapa[chave];
    return valor != null && valor.toString().trim().isNotEmpty;
  }

  bool temDadosOpenFoodFacts(Map<String, dynamic> bebida) {
    return [
      'nutri_score',
      'nova_grupo',
      'eco_score',
      'alergenos',
      'categorias',
      'quantidade',
      'embalagem',
      'paises',
    ].any((chave) => temTexto(bebida, chave));
  }

  @override
  Widget build(BuildContext context) {
    final bebida =
        ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    final cachaca = bebida['cachaca'] is Map && tipoEhCachaca(bebida['tipo'])
        ? Map<String, dynamic>.from(bebida['cachaca'] as Map)
        : null;

    return Scaffold(
      appBar: AppBar(
        title: Text(bebida['nome'] ?? 'Bebida'),
        actions: [
          IconButton(
            tooltip: 'Completar dados da bebida',
            onPressed: () => completarDados(bebida),
            icon: const Icon(Icons.edit_note),
          ),
          IconButton(
            tooltip: 'Adicionar aos favoritos',
            onPressed: () => favoritar(bebida),
            icon: const Icon(Icons.favorite_border),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: [
            _BeverageHeader(bebida: bebida),
            const SizedBox(height: 12),
            _InfoSection(
              icon: Icons.info_outline,
              title: 'Informações',
              children: [
                _InfoRow(label: 'Marca', value: textoCampo(bebida['marca'])),
                _InfoRow(label: 'Tipo', value: textoCampo(bebida['tipo'])),
                _InfoRow(
                  label: 'Código de barras',
                  value: textoCampo(bebida['codigo_barras']),
                ),
                _InfoRow(
                  label: 'Teor alcoólico',
                  value: textoCampo(bebida['teor_alcoolico'], sufixo: '%'),
                ),
              ],
            ),
            _InfoSection(
              icon: Icons.receipt_long_outlined,
              title: 'Ingredientes',
              children: [
                Text(
                  textoCampo(bebida['ingredientes']),
                  style: const TextStyle(height: 1.35),
                ),
              ],
            ),
            if (temDadosOpenFoodFacts(bebida))
              _InfoSection(
                icon: Icons.public,
                title: 'Dados externos',
                subtitle: 'Open Food Facts',
                children: [
                  if (temTexto(bebida, 'paises'))
                    _InfoRow(
                        label: 'País', value: textoCampo(bebida['paises'])),
                  if (temTexto(bebida, 'nutri_score'))
                    _InfoRow(
                      label: 'Nutri-Score',
                      value: bebida['nutri_score'].toString().toUpperCase(),
                    ),
                  if (temTexto(bebida, 'nova_grupo'))
                    _InfoRow(
                        label: 'Grupo NOVA', value: '${bebida['nova_grupo']}'),
                  if (temTexto(bebida, 'eco_score'))
                    _InfoRow(
                      label: 'Eco-Score',
                      value: bebida['eco_score'].toString().toUpperCase(),
                    ),
                  if (temTexto(bebida, 'alergenos'))
                    _InfoRow(
                        label: 'Alérgenos',
                        value: textoCampo(bebida['alergenos'])),
                  if (temTexto(bebida, 'categorias'))
                    _InfoRow(
                        label: 'Categorias',
                        value: textoCampo(bebida['categorias'])),
                  if (temTexto(bebida, 'quantidade'))
                    _InfoRow(
                        label: 'Quantidade',
                        value: textoCampo(bebida['quantidade'])),
                  if (temTexto(bebida, 'embalagem'))
                    _InfoRow(
                        label: 'Embalagem',
                        value: textoCampo(bebida['embalagem'])),
                ],
              ),
            if (cachaca != null)
              _InfoSection(
                icon: Icons.liquor_outlined,
                title: 'Dados de cachaça',
                children: [
                  _InfoRow(
                      label: 'Volume',
                      value: textoCampo(cachaca['volume_ml'], sufixo: ' ml')),
                  _InfoRow(
                      label: 'Classificação',
                      value: textoCampo(cachaca['classificacao'])),
                  _InfoRow(
                      label: 'Madeira', value: textoCampo(cachaca['madeira'])),
                  _InfoRow(
                    label: 'Envelhecimento',
                    value: textoCampo(cachaca['tempo_envelhecimento_meses'],
                        sufixo: ' meses'),
                  ),
                  _InfoRow(
                      label: 'Cidade',
                      value: textoCampo(cachaca['cidade_origem'])),
                  _InfoRow(
                      label: 'Estado',
                      value: textoCampo(cachaca['estado_origem'])),
                  _InfoRow(
                      label: 'Região',
                      value: textoCampo(cachaca['regiao_origem'])),
                  _InfoRow(
                      label: 'Alambique',
                      value: textoCampo(cachaca['alambique'])),
                  _InfoRow(
                      label: 'Produtor',
                      value: textoCampo(cachaca['produtor'])),
                  _InfoRow(label: 'Lote', value: textoCampo(cachaca['lote'])),
                ],
              ),
            _InfoSection(
              icon: Icons.star_outline,
              title: 'Minha avaliação',
              children: [
                DropdownButtonFormField<int>(
                  initialValue: nota,
                  decoration: const InputDecoration(labelText: 'Nota'),
                  items: const [
                    DropdownMenuItem(value: 1, child: Text('1 - Muito ruim')),
                    DropdownMenuItem(value: 2, child: Text('2 - Ruim')),
                    DropdownMenuItem(value: 3, child: Text('3 - Regular')),
                    DropdownMenuItem(value: 4, child: Text('4 - Boa')),
                    DropdownMenuItem(value: 5, child: Text('5 - Excelente')),
                  ],
                  onChanged: (valor) => setState(() => nota = valor ?? 5),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: comentarioController,
                  decoration: const InputDecoration(
                    labelText: 'Comentário',
                    hintText: 'Escreva sua opinião sobre a bebida',
                  ),
                  maxLines: 4,
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Compraria novamente?'),
                  value: comprariaNovamente,
                  onChanged: (valor) =>
                      setState(() => comprariaNovamente = valor),
                ),
                const SizedBox(height: 8),
                FilledButton.icon(
                  onPressed: salvando ? null : () => avaliar(bebida),
                  icon: const Icon(Icons.save_outlined),
                  label: Text(salvando ? 'Salvando...' : 'Salvar avaliação'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String textoCampo(dynamic valor, {String sufixo = ''}) {
    if (valor == null) return 'Não informado';
    final texto = valor.toString().trim();
    if (texto.isEmpty) return 'Não informado';
    return '$texto$sufixo';
  }
}

class _BeverageHeader extends StatelessWidget {
  const _BeverageHeader({required this.bebida});

  final Map<String, dynamic> bebida;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final imagem = bebida['imagem_url']?.toString();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.primary,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 96,
            height: 128,
            decoration: BoxDecoration(
              color: const Color(0xfffffbf5),
              borderRadius: BorderRadius.circular(8),
            ),
            clipBehavior: Clip.antiAlias,
            child: imagem == null || imagem.isEmpty
                ? const Icon(Icons.local_drink_outlined, size: 42)
                : Image.network(
                    imagem,
                    fit: BoxFit.contain,
                    semanticLabel: 'Imagem do rótulo da bebida',
                    errorBuilder: (_, __, ___) =>
                        const Icon(Icons.local_drink_outlined, size: 42),
                  ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  bebida['nome'] ?? 'Nome não informado',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 23,
                    fontWeight: FontWeight.w800,
                    height: 1.08,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  bebida['marca'] ?? 'Marca não informada',
                  style: const TextStyle(color: Color(0xfffff4e8)),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    _HeaderBadge(label: bebida['tipo'] ?? 'bebida'),
                    if ((bebida['paises'] ?? '').toString().isNotEmpty)
                      const _HeaderBadge(label: 'Brasil'),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _HeaderBadge extends StatelessWidget {
  const _HeaderBadge({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: const Color(0xfff3b35f),
        borderRadius: BorderRadius.circular(99),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: Color(0xff241611),
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}

class _InfoSection extends StatelessWidget {
  const _InfoSection({
    required this.icon,
    required this.title,
    required this.children,
    this.subtitle,
  });

  final IconData icon;
  final String title;
  final String? subtitle;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                if (subtitle != null)
                  Text(
                    subtitle!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            ...children,
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}

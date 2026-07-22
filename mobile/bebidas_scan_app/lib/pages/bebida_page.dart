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
          padding: const EdgeInsets.all(16),
          children: [
            if (bebida['imagem_url'] != null)
              Image.network(
                bebida['imagem_url'],
                height: 220,
                fit: BoxFit.contain,
                semanticLabel: 'Imagem do rótulo da bebida',
                errorBuilder: (_, __, ___) => const SizedBox.shrink(),
              ),
            const SizedBox(height: 16),
            Text(
              bebida['nome'] ?? 'Nome não informado',
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text('Marca: ${bebida['marca'] ?? 'Não informada'}'),
            Text('Tipo: ${bebida['tipo'] ?? 'Não informado'}'),
            Text(
                'Código de barras: ${bebida['codigo_barras'] ?? 'Não informado'}'),
            Text(
                'Teor alcoólico: ${textoCampo(bebida['teor_alcoolico'], sufixo: '%')}'),
            const SizedBox(height: 16),
            Text('Ingredientes: ${bebida['ingredientes'] ?? 'Não informado'}'),
            if (temDadosOpenFoodFacts(bebida)) ...[
              const Divider(height: 32),
              const Text(
                'Dados do Open Food Facts',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              if (temTexto(bebida, 'nutri_score'))
                Text(
                    'Nutri-Score: ${bebida['nutri_score'].toString().toUpperCase()}'),
              if (temTexto(bebida, 'nova_grupo'))
                Text('Grupo NOVA: ${bebida['nova_grupo']}'),
              if (temTexto(bebida, 'eco_score'))
                Text(
                    'Eco-Score: ${bebida['eco_score'].toString().toUpperCase()}'),
              if (temTexto(bebida, 'alergenos'))
                Text('Alérgenos: ${bebida['alergenos']}'),
              if (temTexto(bebida, 'categorias'))
                Text('Categorias: ${bebida['categorias']}'),
              if (temTexto(bebida, 'quantidade'))
                Text('Quantidade: ${bebida['quantidade']}'),
              if (temTexto(bebida, 'embalagem'))
                Text('Embalagem: ${bebida['embalagem']}'),
              if (temTexto(bebida, 'paises'))
                Text('Países: ${bebida['paises']}'),
            ],
            if (cachaca != null) ...[
              const Divider(height: 32),
              const Text(
                'Dados de cachaça',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                  'Volume: ${textoCampo(cachaca['volume_ml'], sufixo: ' ml')}'),
              Text(
                  'Classificação: ${cachaca['classificacao'] ?? 'Não informada'}'),
              Text('Madeira: ${cachaca['madeira'] ?? 'Não informada'}'),
              Text(
                  'Envelhecimento: ${textoCampo(cachaca['tempo_envelhecimento_meses'], sufixo: ' meses')}'),
              Text(
                  'Cidade de origem: ${cachaca['cidade_origem'] ?? 'Não informada'}'),
              Text(
                  'Estado de origem: ${cachaca['estado_origem'] ?? 'Não informado'}'),
              Text('Região: ${cachaca['regiao_origem'] ?? 'Não informada'}'),
              Text('Alambique: ${cachaca['alambique'] ?? 'Não informado'}'),
              Text('Produtor: ${cachaca['produtor'] ?? 'Não informado'}'),
              Text('Lote: ${cachaca['lote'] ?? 'Não informado'}'),
            ],
            const Divider(height: 32),
            const Text(
              'Minha avaliação',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
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
              onChanged: (valor) => setState(() => comprariaNovamente = valor),
            ),
            const SizedBox(height: 20),
            FilledButton(
              onPressed: salvando ? null : () => avaliar(bebida),
              child: Text(salvando ? 'Salvando...' : 'Salvar avaliação'),
            ),
          ],
        ),
      ),
    );
  }

  String textoCampo(dynamic valor, {String sufixo = ''}) {
    if (valor == null) return 'Não informado';
    final texto = valor.toString();
    if (texto.isEmpty) return 'Não informado';
    return '$texto$sufixo';
  }
}

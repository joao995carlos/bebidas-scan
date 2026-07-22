import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/token_service.dart';

class BebidaFormPage extends StatefulWidget {
  const BebidaFormPage({super.key});

  @override
  State<BebidaFormPage> createState() => _BebidaFormPageState();
}

class _BebidaFormPageState extends State<BebidaFormPage> {
  final api = ApiService();
  final tokenService = TokenService();
  final nomeController = TextEditingController();
  final marcaController = TextEditingController();
  final codigoController = TextEditingController();
  final teorController = TextEditingController();
  final volumeController = TextEditingController();
  final ingredientesController = TextEditingController();
  final imagemController = TextEditingController();
  final classificacaoController = TextEditingController();
  final madeiraController = TextEditingController();
  final envelhecimentoController = TextEditingController();
  final cidadeController = TextEditingController();
  final estadoController = TextEditingController();
  final regiaoController = TextEditingController();
  final alambiqueController = TextEditingController();
  final produtorController = TextEditingController();
  final loteController = TextEditingController();

  bool inicializado = false;
  bool salvando = false;
  String? erro;
  String tipoSelecionado = 'cachaca';
  Map<String, dynamic>? bebidaExistente;

  bool get tipoEhCachaca =>
      tipoSelecionado == 'cachaca' || tipoSelecionado == 'aguardente';

  @override
  void dispose() {
    nomeController.dispose();
    marcaController.dispose();
    codigoController.dispose();
    teorController.dispose();
    volumeController.dispose();
    ingredientesController.dispose();
    imagemController.dispose();
    classificacaoController.dispose();
    madeiraController.dispose();
    envelhecimentoController.dispose();
    cidadeController.dispose();
    estadoController.dispose();
    regiaoController.dispose();
    alambiqueController.dispose();
    produtorController.dispose();
    loteController.dispose();
    super.dispose();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (inicializado) return;
    inicializado = true;

    final args = ModalRoute.of(context)?.settings.arguments;
    if (args is Map) {
      final dados = Map<String, dynamic>.from(args);
      if (dados['bebida'] is Map) {
        bebidaExistente = Map<String, dynamic>.from(dados['bebida'] as Map);
        preencherComBebida(bebidaExistente!);
      }

      if (dados['sugestao'] is Map) {
        preencherComBebida(
          Map<String, dynamic>.from(dados['sugestao'] as Map),
        );
      }

      final codigo = dados['codigo_barras']?.toString();
      if (codigo != null && codigo.isNotEmpty) {
        codigoController.text = codigo;
      }
    }
  }

  void preencherComBebida(Map<String, dynamic> bebida) {
    final cachaca = bebida['cachaca'] is Map
        ? Map<String, dynamic>.from(bebida['cachaca'] as Map)
        : <String, dynamic>{};

    nomeController.text = valorTexto(bebida['nome']);
    marcaController.text = valorTexto(bebida['marca']);
    tipoSelecionado =
        tipoValido(valorTexto(bebida['tipo'], fallback: 'cachaca'));
    codigoController.text = valorTexto(bebida['codigo_barras']);
    teorController.text = valorTexto(bebida['teor_alcoolico']);
    ingredientesController.text = valorTexto(bebida['ingredientes']);
    imagemController.text = valorTexto(bebida['imagem_url']);
    volumeController.text = valorTexto(cachaca['volume_ml']);
    classificacaoController.text = valorTexto(cachaca['classificacao']);
    madeiraController.text = valorTexto(cachaca['madeira']);
    envelhecimentoController.text =
        valorTexto(cachaca['tempo_envelhecimento_meses']);
    cidadeController.text = valorTexto(cachaca['cidade_origem']);
    estadoController.text = valorTexto(cachaca['estado_origem']);
    regiaoController.text = valorTexto(cachaca['regiao_origem']);
    alambiqueController.text = valorTexto(cachaca['alambique']);
    produtorController.text = valorTexto(cachaca['produtor']);
    loteController.text = valorTexto(cachaca['lote']);
  }

  String tipoValido(String valor) {
    const tipos = {
      'cachaca',
      'aguardente',
      'cerveja',
      'vinho',
      'whisky',
      'vodka',
      'gin',
      'rum',
      'licor',
      'outro',
    };
    return tipos.contains(valor) ? valor : 'outro';
  }

  String valorTexto(dynamic valor, {String fallback = ''}) {
    if (valor == null) return fallback;
    return valor.toString();
  }

  Future<bool> exigirConta() async {
    final token = await tokenService.lerAccessToken();
    if (token != null) return true;

    if (!mounted) return false;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('Entre ou crie uma conta para cadastrar bebidas.'),
        action: SnackBarAction(
          label: 'Entrar',
          onPressed: () => Navigator.pushReplacementNamed(context, '/login'),
        ),
      ),
    );
    return false;
  }

  Map<String, dynamic> montarPayload() {
    final payload = {
      'nome': textoOuNull(nomeController),
      'marca': textoOuNull(marcaController),
      'tipo': tipoSelecionado,
      'codigo_barras': textoOuNull(codigoController),
      'teor_alcoolico': numeroDoubleOuNull(teorController),
      'ingredientes': textoOuNull(ingredientesController),
      'imagem_url': textoOuNull(imagemController),
    }..removeWhere((_, valor) => valor == null);

    if (tipoEhCachaca) {
      final cachaca = {
        'volume_ml': numeroIntOuNull(volumeController),
        'classificacao': textoOuNull(classificacaoController),
        'madeira': textoOuNull(madeiraController),
        'tempo_envelhecimento_meses': numeroIntOuNull(envelhecimentoController),
        'cidade_origem': textoOuNull(cidadeController),
        'estado_origem': textoOuNull(estadoController)?.toUpperCase(),
        'regiao_origem': textoOuNull(regiaoController),
        'alambique': textoOuNull(alambiqueController),
        'produtor': textoOuNull(produtorController),
        'lote': textoOuNull(loteController),
      }..removeWhere((_, valor) => valor == null);

      if (cachaca.isNotEmpty) {
        payload['cachaca'] = cachaca;
      }
    }

    return payload;
  }

  String? textoOuNull(TextEditingController controller) {
    final texto = controller.text.trim();
    return texto.isEmpty ? null : texto;
  }

  double? numeroDoubleOuNull(TextEditingController controller) {
    final texto = controller.text.trim().replaceAll(',', '.');
    if (texto.isEmpty) return null;
    return double.tryParse(texto);
  }

  int? numeroIntOuNull(TextEditingController controller) {
    final texto = controller.text.trim();
    if (texto.isEmpty) return null;
    return int.tryParse(texto);
  }

  Future<void> salvar() async {
    if (!await exigirConta()) return;

    setState(() {
      salvando = true;
      erro = null;
    });

    try {
      final payload = montarPayload();
      final Response resposta;
      final existente = bebidaExistente;

      if (existente == null) {
        resposta = await api.criarBebida(payload);
      } else {
        resposta = await api.atualizarBebida(existente['id_bebida'], payload);
      }

      if (!mounted) return;
      Navigator.pushReplacementNamed(
        context,
        '/bebida',
        arguments: Map<String, dynamic>.from(resposta.data),
      );
    } on DioException catch (e) {
      if (!mounted) return;
      final status = e.response?.statusCode;
      setState(() {
        erro = status == 401
            ? 'Entre ou crie uma conta para salvar.'
            : 'Não foi possível salvar. Confira os campos e tente novamente.';
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        erro = 'Não foi possível salvar. Tente novamente.';
      });
    } finally {
      if (mounted) setState(() => salvando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final editando = bebidaExistente != null;

    return Scaffold(
      appBar: AppBar(
        title: Text(editando ? 'Completar dados' : 'Cadastrar bebida'),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              editando
                  ? 'Revise ou complete as informações da bebida.'
                  : 'Informe os dados principais da bebida encontrada.',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            campo(nomeController, 'Nome da bebida', obrigatorio: true),
            campo(marcaController, 'Marca'),
            DropdownButtonFormField<String>(
              initialValue: tipoSelecionado,
              decoration: const InputDecoration(labelText: 'Tipo *'),
              items: const [
                DropdownMenuItem(value: 'cachaca', child: Text('Cachaça')),
                DropdownMenuItem(
                    value: 'aguardente', child: Text('Aguardente')),
                DropdownMenuItem(value: 'cerveja', child: Text('Cerveja')),
                DropdownMenuItem(value: 'vinho', child: Text('Vinho')),
                DropdownMenuItem(value: 'whisky', child: Text('Whisky')),
                DropdownMenuItem(value: 'vodka', child: Text('Vodka')),
                DropdownMenuItem(value: 'gin', child: Text('Gin')),
                DropdownMenuItem(value: 'rum', child: Text('Rum')),
                DropdownMenuItem(value: 'licor', child: Text('Licor')),
                DropdownMenuItem(value: 'outro', child: Text('Outra bebida')),
              ],
              onChanged: (valor) {
                if (valor == null) return;
                setState(() => tipoSelecionado = valor);
              },
            ),
            const SizedBox(height: 12),
            campo(codigoController, 'Código de barras',
                tipo: TextInputType.number),
            campo(teorController, 'Teor alcoólico (%)',
                tipo: const TextInputType.numberWithOptions(decimal: true)),
            campo(ingredientesController, 'Ingredientes', linhas: 3),
            campo(imagemController, 'URL da imagem'),
            if (tipoEhCachaca) ...[
              const Divider(height: 32),
              const Text(
                'Dados de cachaça',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              campo(volumeController, 'Volume da garrafa (ml)',
                  tipo: TextInputType.number),
              campo(classificacaoController, 'Classificação'),
              campo(madeiraController, 'Madeira'),
              campo(envelhecimentoController, 'Tempo de envelhecimento (meses)',
                  tipo: TextInputType.number),
              campo(cidadeController, 'Cidade de origem'),
              campo(estadoController, 'Estado de origem (UF)'),
              campo(regiaoController, 'Região de origem'),
              campo(alambiqueController, 'Alambique'),
              campo(produtorController, 'Produtor'),
              campo(loteController, 'Lote'),
            ],
            if (erro != null) ...[
              const SizedBox(height: 12),
              Text(erro!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: salvando ? null : salvar,
              icon: const Icon(Icons.save),
              label: Text(salvando ? 'Salvando...' : 'Salvar bebida'),
            ),
          ],
        ),
      ),
    );
  }

  Widget campo(
    TextEditingController controller,
    String label, {
    bool obrigatorio = false,
    TextInputType? tipo,
    int linhas = 1,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextField(
        controller: controller,
        keyboardType: tipo,
        maxLines: linhas,
        decoration: InputDecoration(
          labelText: obrigatorio ? '$label *' : label,
        ),
      ),
    );
  }
}

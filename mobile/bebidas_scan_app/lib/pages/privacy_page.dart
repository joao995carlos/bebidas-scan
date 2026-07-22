import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import '../services/api_service.dart';
import '../services/token_service.dart';

class PrivacyPage extends StatefulWidget {
  const PrivacyPage({super.key});

  @override
  State<PrivacyPage> createState() => _PrivacyPageState();
}

class _PrivacyPageState extends State<PrivacyPage> {
  final api = ApiService();
  final tokenService = TokenService();
  final emailController = TextEditingController();
  final senhaController = TextEditingController();
  final categorias = <String, bool>{
    'perfil': true,
    'avaliacoes': true,
    'favoritos': true,
    'precos': true,
    'bebidas': true,
  };

  bool carregando = true;
  bool processando = false;
  Map<String, dynamic>? status;
  String? erro;
  String? csvExportado;
  String? arquivoCsv;
  static final emailRegex = RegExp(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$",
  );

  @override
  void initState() {
    super.initState();
    carregarStatus();
  }

  @override
  void dispose() {
    emailController.dispose();
    senhaController.dispose();
    super.dispose();
  }

  Future<void> carregarStatus() async {
    try {
      final resposta = await api.statusLgpd();
      if (!mounted) return;
      setState(() {
        status = Map<String, dynamic>.from(resposta.data);
        carregando = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        erro = 'Não foi possível carregar seus dados de privacidade.';
        carregando = false;
      });
    }
  }

  Future<void> exportar() async {
    final selecionadas = categorias.entries
        .where((item) => item.value)
        .map((item) => item.key)
        .toList();
    if (selecionadas.isEmpty) {
      setState(() => erro = 'Selecione pelo menos uma categoria.');
      return;
    }

    setState(() {
      processando = true;
      erro = null;
      csvExportado = null;
      arquivoCsv = null;
    });

    try {
      final resposta = await api.exportarDadosCsv(selecionadas);
      final csv = resposta.data?.toString() ?? '';
      final arquivo = await salvarCsvTemporario(csv);
      if (!mounted) return;
      setState(() {
        csvExportado = csv;
        arquivoCsv = arquivo.path;
      });
      await compartilharArquivo(arquivo);
    } catch (_) {
      if (!mounted) return;
      setState(() => erro = 'Não foi possível exportar os dados.');
    } finally {
      if (mounted) setState(() => processando = false);
    }
  }

  Future<File> salvarCsvTemporario(String csv) async {
    final diretorio = await getTemporaryDirectory();
    final agora = DateTime.now();
    final nome =
        'bebidas-scan-dados-${agora.year}${agora.month.toString().padLeft(2, '0')}${agora.day.toString().padLeft(2, '0')}-${agora.hour.toString().padLeft(2, '0')}${agora.minute.toString().padLeft(2, '0')}${agora.second.toString().padLeft(2, '0')}.csv';
    final arquivo = File('${diretorio.path}${Platform.pathSeparator}$nome');
    return arquivo.writeAsString(csv, flush: true);
  }

  Future<void> compartilharArquivo(File arquivo) async {
    await SharePlus.instance.share(
      ShareParams(
        files: [XFile(arquivo.path, mimeType: 'text/csv')],
        subject: 'Meus dados do Bebidas Scan',
        text: 'Exportação dos meus dados do Bebidas Scan em CSV.',
      ),
    );
  }

  Future<void> copiarCsv() async {
    final csv = csvExportado;
    if (csv == null || csv.isEmpty) return;
    await Clipboard.setData(ClipboardData(text: csv));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
          content: Text('CSV copiado para a área de transferência.')),
    );
  }

  Future<void> compartilharCsvSalvo() async {
    final path = arquivoCsv;
    if (path == null) return;
    await compartilharArquivo(File(path));
  }

  Future<void> anonimizar() async {
    final email = emailController.text.trim().toLowerCase();
    if (!emailRegex.hasMatch(email) || email.length > 150) {
      setState(() => erro = 'Informe um e-mail válido.');
      return;
    }

    final confirmado = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Excluir e anonimizar conta?'),
        content: const Text(
          'Esta ação desativa sua conta, revoga sessões, apaga favoritos e remove vínculos pessoais. Ela não pode ser desfeita.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Confirmar'),
          ),
        ],
      ),
    );
    if (confirmado != true) return;

    setState(() {
      processando = true;
      erro = null;
    });

    try {
      await api.anonimizarConta(
        email: email,
        senha: senhaController.text,
      );
      await tokenService.limparTokens();
      if (!mounted) return;
      Navigator.pushNamedAndRemoveUntil(context, '/login', (_) => false);
    } on DioException catch (e) {
      if (!mounted) return;
      setState(() {
        erro = e.response?.statusCode == 403
            ? 'E-mail ou senha não conferem.'
            : 'Não foi possível excluir a conta.';
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => erro = 'Não foi possível excluir a conta.');
    } finally {
      if (mounted) setState(() => processando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final dados = status;

    return Scaffold(
      appBar: AppBar(title: const Text('Minha privacidade')),
      body: SafeArea(
        child: carregando
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (erro != null) ...[
                    Text(erro!,
                        style: TextStyle(
                            color: Theme.of(context).colorScheme.error)),
                    const SizedBox(height: 12),
                  ],
                  if (dados != null) ...[
                    const Text(
                      'Status LGPD',
                      style:
                          TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text('Versão atual: ${dados['versao_atual'] ?? ''}'),
                    Text(
                        'Política aceita: ${dados['privacidade_versao_aceita'] ?? 'pendente'}'),
                    Text(
                        'Termos aceitos: ${dados['termos_versao_aceita'] ?? 'pendente'}'),
                    Text('Aceite em: ${dados['lgpd_aceite_em'] ?? 'pendente'}'),
                    const SizedBox(height: 8),
                    OutlinedButton.icon(
                      onPressed: () =>
                          Navigator.pushNamed(context, '/lgpd-aceitar'),
                      icon: const Icon(Icons.edit),
                      label: const Text('Atualizar preferências'),
                    ),
                    const SizedBox(height: 16),
                  ],
                  const Text(
                    'Exportar meus dados',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  for (final item in categorias.keys)
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(labelCategoria(item)),
                      value: categorias[item],
                      onChanged: (valor) {
                        setState(() => categorias[item] = valor ?? false);
                      },
                    ),
                  FilledButton.icon(
                    onPressed: processando ? null : exportar,
                    icon: const Icon(Icons.ios_share),
                    label: const Text('Gerar e compartilhar CSV'),
                  ),
                  if (csvExportado != null) ...[
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        OutlinedButton.icon(
                          onPressed: copiarCsv,
                          icon: const Icon(Icons.copy),
                          label: const Text('Copiar CSV'),
                        ),
                        OutlinedButton.icon(
                          onPressed: compartilharCsvSalvo,
                          icon: const Icon(Icons.share),
                          label: const Text('Compartilhar arquivo'),
                        ),
                      ],
                    ),
                    if (arquivoCsv != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        'Arquivo gerado: $arquivoCsv',
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                    const SizedBox(height: 8),
                    Container(
                      width: double.infinity,
                      constraints: const BoxConstraints(maxHeight: 220),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        border: Border.all(
                          color: Theme.of(context).colorScheme.outline,
                        ),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: SingleChildScrollView(
                        child: SelectableText(csvExportado!),
                      ),
                    ),
                  ],
                  const Divider(height: 32),
                  const Text(
                    'Excluir minha conta',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Para confirmar, informe o e-mail e a senha da conta.',
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: emailController,
                    decoration: const InputDecoration(
                      labelText: 'E-mail',
                      helperText: 'Exemplo: nome@email.com',
                    ),
                    keyboardType: TextInputType.emailAddress,
                    autocorrect: false,
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: senhaController,
                    decoration: const InputDecoration(labelText: 'Senha'),
                    obscureText: true,
                  ),
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    onPressed: processando ? null : anonimizar,
                    icon: const Icon(Icons.delete_forever),
                    label: const Text('Excluir e anonimizar conta'),
                  ),
                ],
              ),
      ),
    );
  }

  String labelCategoria(String categoria) {
    return switch (categoria) {
      'perfil' => 'Perfil',
      'avaliacoes' => 'Avaliações',
      'favoritos' => 'Favoritos',
      'precos' => 'Preços',
      'bebidas' => 'Bebidas cadastradas',
      _ => categoria,
    };
  }
}

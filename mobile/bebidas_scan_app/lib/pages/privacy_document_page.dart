import 'package:flutter/material.dart';

import '../services/api_service.dart';

class PrivacyDocumentPage extends StatefulWidget {
  const PrivacyDocumentPage({super.key});

  @override
  State<PrivacyDocumentPage> createState() => _PrivacyDocumentPageState();
}

class _PrivacyDocumentPageState extends State<PrivacyDocumentPage> {
  final api = ApiService();
  bool carregando = true;
  String tipo = 'politica';
  String titulo = 'Documento';
  String versao = '';
  String texto = '';
  String? erro;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final args = ModalRoute.of(context)?.settings.arguments;
    tipo = args is Map ? args['tipo']?.toString() ?? 'politica' : 'politica';
    if (texto.isEmpty && erro == null) carregar();
  }

  Future<void> carregar() async {
    setState(() {
      carregando = true;
      erro = null;
    });

    try {
      final resposta = tipo == 'termos'
          ? await api.termosUso()
          : await api.politicaPrivacidade();
      if (!mounted) return;
      setState(() {
        titulo = tipo == 'termos' ? 'Termos de Uso' : 'Política de Privacidade';
        versao = resposta.data['versao']?.toString() ?? '';
        texto = resposta.data['texto']?.toString() ?? '';
        carregando = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        titulo = tipo == 'termos' ? 'Termos de Uso' : 'Política de Privacidade';
        erro =
            'Não foi possível carregar este documento. Verifique a conexão e tente novamente.';
        carregando = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: Text(titulo)),
      body: SafeArea(
        child: carregando
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(16),
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
                        Icon(
                          tipo == 'termos'
                              ? Icons.article_outlined
                              : Icons.privacy_tip_outlined,
                          color: Colors.white,
                          size: 34,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          titulo,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 26,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        if (versao.isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(
                            'Versão $versao',
                            style: const TextStyle(color: Color(0xffffead1)),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (erro != null)
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              erro!,
                              style: TextStyle(color: colors.error),
                            ),
                            const SizedBox(height: 12),
                            FilledButton.icon(
                              onPressed: carregar,
                              icon: const Icon(Icons.refresh),
                              label: const Text('Tentar novamente'),
                            ),
                          ],
                        ),
                      ),
                    )
                  else
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Text(
                          texto,
                          style: const TextStyle(fontSize: 16, height: 1.45),
                        ),
                      ),
                    ),
                ],
              ),
      ),
    );
  }
}

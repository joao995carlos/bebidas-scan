import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../widgets/legal_acceptance_tile.dart';

class LgpdAcceptPage extends StatefulWidget {
  const LgpdAcceptPage({super.key});

  @override
  State<LgpdAcceptPage> createState() => _LgpdAcceptPageState();
}

class _LgpdAcceptPageState extends State<LgpdAcceptPage> {
  final api = ApiService();
  DateTime? dataNascimento;
  bool aceitouPrivacidade = false;
  bool aceitouTermos = false;
  bool marketingConsentimento = false;
  bool salvando = false;
  String? erro;

  Future<void> escolherDataNascimento() async {
    final hoje = DateTime.now();
    final selecionada = await showDatePicker(
      context: context,
      initialDate: DateTime(hoje.year - 18, hoje.month, hoje.day),
      firstDate: DateTime(1900),
      lastDate: hoje,
    );
    if (selecionada != null) {
      setState(() => dataNascimento = selecionada);
    }
  }

  String dataApi() {
    final data = dataNascimento!;
    return '${data.year}-${data.month.toString().padLeft(2, '0')}-${data.day.toString().padLeft(2, '0')}';
  }

  bool maiorDe18() {
    final data = dataNascimento;
    if (data == null) return false;
    final hoje = DateTime.now();
    var idade = hoje.year - data.year;
    if (hoje.month < data.month ||
        (hoje.month == data.month && hoje.day < data.day)) {
      idade--;
    }
    return idade >= 18;
  }

  Future<void> aceitar() async {
    if (dataNascimento == null) {
      setState(() => erro = 'Informe sua data de nascimento.');
      return;
    }
    if (!maiorDe18()) {
      setState(() => erro = 'O Bebidas Scan é destinado a maiores de 18 anos.');
      return;
    }
    if (!aceitouPrivacidade || !aceitouTermos) {
      setState(
          () => erro = 'Aceite a Política de Privacidade e os Termos de Uso.');
      return;
    }

    setState(() {
      salvando = true;
      erro = null;
    });

    try {
      await api.aceitarLgpd(
        dataNascimento: dataApi(),
        aceitouPrivacidade: aceitouPrivacidade,
        aceitouTermos: aceitouTermos,
        marketingConsentimento: marketingConsentimento,
      );
      if (!mounted) return;
      Navigator.pushReplacementNamed(context, '/home');
    } catch (_) {
      if (!mounted) return;
      setState(() => erro = 'Não foi possível registrar o aceite.');
    } finally {
      if (mounted) setState(() => salvando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final dataLabel = dataNascimento == null
        ? 'Selecionar data'
        : '${dataNascimento!.day.toString().padLeft(2, '0')}/'
            '${dataNascimento!.month.toString().padLeft(2, '0')}/'
            '${dataNascimento!.year}';

    return Scaffold(
      appBar: AppBar(title: const Text('Atualização de privacidade')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Text(
              'Para continuar, confirme os dados de privacidade.',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: escolherDataNascimento,
              icon: const Icon(Icons.calendar_month),
              label: Text('Data de nascimento: $dataLabel'),
            ),
            LegalAcceptanceTile(
              value: aceitouPrivacidade,
              title: 'Aceito a Pol?tica de Privacidade',
              documentLabel: 'Ler Pol?tica de Privacidade',
              onOpenDocument: () => Navigator.pushNamed(
                context,
                '/documento-privacidade',
                arguments: {'tipo': 'politica'},
              ),
              onChanged: (valor) {
                setState(() => aceitouPrivacidade = valor ?? false);
              },
            ),
            LegalAcceptanceTile(
              value: aceitouTermos,
              title: 'Aceito os Termos de Uso',
              documentLabel: 'Ler Termos de Uso',
              onOpenDocument: () => Navigator.pushNamed(
                context,
                '/documento-privacidade',
                arguments: {'tipo': 'termos'},
              ),
              onChanged: (valor) {
                setState(() => aceitouTermos = valor ?? false);
              },
            ),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Aceito receber comunicações e novidades'),
              value: marketingConsentimento,
              onChanged: (valor) {
                setState(() => marketingConsentimento = valor ?? false);
              },
            ),
            if (erro != null) ...[
              const SizedBox(height: 12),
              Text(erro!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
            const SizedBox(height: 20),
            FilledButton(
              onPressed: salvando ? null : aceitar,
              child: Text(salvando ? 'Salvando...' : 'Aceitar e continuar'),
            ),
          ],
        ),
      ),
    );
  }
}

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/token_service.dart';
import '../widgets/legal_acceptance_tile.dart';

class RegisterPage extends StatefulWidget {
  const RegisterPage({super.key});

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final api = ApiService();
  final tokenService = TokenService();
  final nomeController = TextEditingController();
  final nomeUsuarioController = TextEditingController();
  final emailController = TextEditingController();
  final senhaController = TextEditingController();
  DateTime? dataNascimento;
  bool aceitouPrivacidade = false;
  bool aceitouTermos = false;
  bool marketingConsentimento = false;
  bool carregando = false;
  String? erro;

  static final emailRegex = RegExp(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$",
  );
  static final senhaForteRegex =
      RegExp(r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$');

  @override
  void dispose() {
    nomeController.dispose();
    nomeUsuarioController.dispose();
    emailController.dispose();
    senhaController.dispose();
    super.dispose();
  }

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

  String dataNascimentoApi() {
    final data = dataNascimento!;
    final mes = data.month.toString().padLeft(2, '0');
    final dia = data.day.toString().padLeft(2, '0');
    return '${data.year}-$mes-$dia';
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

  String? validarFormulario() {
    final nome = nomeController.text.trim();
    final nomeUsuario = nomeUsuarioController.text.trim();
    final email = emailController.text.trim().toLowerCase();
    final senha = senhaController.text;

    if (nome.length < 2) return 'Informe seu nome.';
    if (nomeUsuario.length < 3) {
      return 'Informe um nome de usuário com pelo menos 3 caracteres.';
    }
    if (!emailRegex.hasMatch(email) || email.length > 150) {
      return 'Informe um e-mail válido.';
    }
    if (!senhaForteRegex.hasMatch(senha)) {
      return 'A senha precisa ter pelo menos 8 caracteres, uma letra maiúscula, um número e um caractere especial.';
    }
    if (dataNascimento == null) return 'Informe sua data de nascimento.';
    if (!maiorDe18()) return 'O Bebidas Scan é destinado a maiores de 18 anos.';
    if (!aceitouPrivacidade || !aceitouTermos) {
      return 'Aceite a Política de Privacidade e os Termos de Uso.';
    }
    return null;
  }

  Future<void> criarConta() async {
    final erroFormulario = validarFormulario();
    if (erroFormulario != null) {
      setState(() => erro = erroFormulario);
      return;
    }

    setState(() {
      carregando = true;
      erro = null;
    });

    try {
      final resposta = await api.registrar(
        nome: nomeController.text.trim(),
        nomeUsuario: nomeUsuarioController.text.trim(),
        email: emailController.text.trim().toLowerCase(),
        senha: senhaController.text,
        dataNascimento: dataNascimentoApi(),
        aceitouPrivacidade: aceitouPrivacidade,
        aceitouTermos: aceitouTermos,
        marketingConsentimento: marketingConsentimento,
      );
      await tokenService.salvarTokens(
        accessToken: resposta.data['access_token'],
        refreshToken: resposta.data['refresh_token'],
      );

      if (!mounted) return;
      Navigator.pushReplacementNamed(context, '/home');
    } on DioException catch (erroDio) {
      final detalhe = erroDio.response?.data is Map
          ? erroDio.response?.data['detail']
          : null;
      setState(() =>
          erro = detalhe?.toString() ?? 'Não foi possível criar a conta.');
    } catch (_) {
      setState(() => erro = 'Não foi possível criar a conta.');
    } finally {
      if (mounted) setState(() => carregando = false);
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
      appBar: AppBar(title: const Text('Criar conta')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextField(
              controller: nomeController,
              decoration: const InputDecoration(labelText: 'Nome'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: nomeUsuarioController,
              decoration: const InputDecoration(labelText: 'Nome de usuário'),
              textInputAction: TextInputAction.next,
              autocorrect: false,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: emailController,
              decoration: const InputDecoration(
                labelText: 'E-mail',
                helperText: 'Exemplo: nome@email.com',
              ),
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.next,
              autocorrect: false,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: senhaController,
              decoration: const InputDecoration(
                labelText: 'Senha',
                helperText:
                    'Mínimo 8 caracteres, letra maiúscula, número e especial.',
              ),
              obscureText: true,
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: escolherDataNascimento,
              icon: const Icon(Icons.calendar_month),
              label: Text('Data de nascimento: $dataLabel'),
            ),
            const SizedBox(height: 8),
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
              Text(
                erro!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: 20),
            FilledButton(
              onPressed: carregando ? null : criarConta,
              child: Text(carregando ? 'Criando...' : 'Criar conta'),
            ),
          ],
        ),
      ),
    );
  }
}

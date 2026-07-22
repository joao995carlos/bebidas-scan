import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../services/api_service.dart';

class ForgotPasswordPage extends StatefulWidget {
  const ForgotPasswordPage({super.key});

  @override
  State<ForgotPasswordPage> createState() => _ForgotPasswordPageState();
}

class _ForgotPasswordPageState extends State<ForgotPasswordPage> {
  final api = ApiService();
  final emailController = TextEditingController();
  bool enviando = false;
  String? mensagem;
  String? erro;

  @override
  void dispose() {
    emailController.dispose();
    super.dispose();
  }

  Future<void> enviar() async {
    final email = emailController.text.trim();
    if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(email)) {
      setState(() {
        erro = 'Digite um e-mail válido.';
        mensagem = null;
      });
      return;
    }

    setState(() {
      enviando = true;
      erro = null;
      mensagem = null;
    });

    try {
      await api.solicitarResetSenha(email);
      if (!mounted) return;
      setState(() {
        mensagem =
            'Se o e-mail estiver cadastrado, enviaremos um link para redefinir a senha.';
      });
    } on DioException catch (e) {
      if (!mounted) return;
      setState(() {
        erro = e.response?.statusCode == 503
            ? 'O envio de e-mail ainda não está configurado no servidor.'
            : 'Não foi possível solicitar a recuperação agora.';
      });
    } finally {
      if (mounted) setState(() => enviando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Recuperar senha')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Text(
              'Informe o e-mail da conta',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            Text(
              'Enviaremos um link temporário para você criar uma nova senha.',
              style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: 20),
            TextField(
              controller: emailController,
              decoration: const InputDecoration(
                labelText: 'E-mail',
                prefixIcon: Icon(Icons.email_outlined),
              ),
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.done,
              onSubmitted: (_) => enviar(),
            ),
            if (erro != null) ...[
              const SizedBox(height: 12),
              Text(erro!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
            if (mensagem != null) ...[
              const SizedBox(height: 12),
              Text(mensagem!, style: const TextStyle(color: Color(0xff1f7a5c))),
            ],
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: enviando ? null : enviar,
              icon: const Icon(Icons.mark_email_read_outlined),
              label: Text(enviando ? 'Enviando...' : 'Enviar link'),
            ),
          ],
        ),
      ),
    );
  }
}

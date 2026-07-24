import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/token_service.dart';

class ChangePasswordPage extends StatefulWidget {
  const ChangePasswordPage({super.key});

  @override
  State<ChangePasswordPage> createState() => _ChangePasswordPageState();
}

class _ChangePasswordPageState extends State<ChangePasswordPage> {
  final api = ApiService();
  final tokenService = TokenService();
  final atualController = TextEditingController();
  final novaController = TextEditingController();
  final confirmarController = TextEditingController();
  bool salvando = false;
  bool senhaAlterada = false;
  String? erro;

  @override
  void dispose() {
    atualController.dispose();
    novaController.dispose();
    confirmarController.dispose();
    super.dispose();
  }

  String? validar() {
    final nova = novaController.text;
    if (atualController.text.isEmpty) return 'Informe sua senha atual.';
    if (!RegExp(r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$')
        .hasMatch(nova)) {
      return 'A nova senha precisa ter 8 caracteres, letra maiúscula, número e caractere especial.';
    }
    if (nova != confirmarController.text) return 'A confirmação não confere.';
    return null;
  }

  Future<void> salvar() async {
    final erroValidacao = validar();
    if (erroValidacao != null) {
      setState(() => erro = erroValidacao);
      return;
    }

    setState(() {
      salvando = true;
      erro = null;
    });

    try {
      await api.alterarSenha(
        senhaAtual: atualController.text,
        novaSenha: novaController.text,
      );
      await tokenService.limparTokens();
      if (!mounted) return;
      setState(() => senhaAlterada = true);
    } on DioException catch (e) {
      if (!mounted) return;
      setState(() {
        erro = e.response?.statusCode == 403
            ? 'Senha atual não confere.'
            : 'Não foi possível alterar a senha.';
      });
    } finally {
      if (mounted) setState(() => salvando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (senhaAlterada) {
      return Scaffold(
        appBar: AppBar(title: const Text('Senha alterada')),
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Icon(
                  Icons.check_circle_outline,
                  size: 64,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(height: 16),
                const Text(
                  'Senha alterada com sucesso',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 8),
                Text(
                  'Por segurança, entre novamente usando sua nova senha.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
                const Spacer(),
                FilledButton.icon(
                  onPressed: () => Navigator.pushNamedAndRemoveUntil(
                      context, '/login', (_) => false),
                  icon: const Icon(Icons.login),
                  label: const Text('Voltar para o login'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Alterar senha')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextField(
              controller: atualController,
              decoration: const InputDecoration(labelText: 'Senha atual'),
              obscureText: true,
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: novaController,
              decoration: const InputDecoration(labelText: 'Nova senha'),
              obscureText: true,
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: confirmarController,
              decoration:
                  const InputDecoration(labelText: 'Confirmar nova senha'),
              obscureText: true,
              onSubmitted: (_) => salvar(),
            ),
            const SizedBox(height: 8),
            const Text(
              'Use pelo menos 8 caracteres, uma letra maiúscula, um número e um caractere especial.',
            ),
            if (erro != null) ...[
              const SizedBox(height: 12),
              Text(erro!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: salvando ? null : salvar,
              icon: const Icon(Icons.lock_reset),
              label: Text(salvando ? 'Salvando...' : 'Alterar senha'),
            ),
          ],
        ),
      ),
    );
  }
}

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/token_service.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final api = ApiService();
  final tokenService = TokenService();
  final identificadorController = TextEditingController();
  final senhaController = TextEditingController();
  bool carregando = false;
  String? erro;
  String? erroTitulo;

  @override
  void dispose() {
    identificadorController.dispose();
    senhaController.dispose();
    super.dispose();
  }

  Future<void> entrar() async {
    final identificador = identificadorController.text.trim();
    final senha = senhaController.text;

    final erroValidacao = validarCampos(
      identificador: identificador,
      senha: senha,
    );
    if (erroValidacao != null) {
      setState(() {
        erroTitulo = erroValidacao.$1;
        erro = erroValidacao.$2;
      });
      return;
    }

    setState(() {
      carregando = true;
      erro = null;
      erroTitulo = null;
    });

    try {
      final resposta = await api.login(
        identificador: identificador,
        senha: senha,
      );
      await tokenService.salvarTokens(
        accessToken: resposta.data['access_token'],
        refreshToken: resposta.data['refresh_token'],
      );
      final status = await api.statusLgpd();

      if (!mounted) return;
      final pendente = status.data['pendente'] == true;
      Navigator.pushReplacementNamed(
        context,
        pendente ? '/lgpd-aceitar' : '/home',
      );
    } on DioException catch (e) {
      if (!mounted) return;
      final mensagem = mensagemErroLogin(e);
      setState(() {
        erroTitulo = mensagem.$1;
        erro = mensagem.$2;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        erroTitulo = 'Não conseguimos entrar agora';
        erro =
            'Ocorreu um erro inesperado. Tente novamente em alguns instantes.';
      });
    } finally {
      if (mounted) setState(() => carregando = false);
    }
  }

  (String, String)? validarCampos({
    required String identificador,
    required String senha,
  }) {
    if (identificador.isEmpty && senha.isEmpty) {
      return (
        'Preencha seus dados',
        'Informe seu nome de usuário e sua senha para entrar.'
      );
    }
    if (identificador.isEmpty) {
      return (
        'Nome de usuário obrigatório',
        'Digite o nome de usuário usado no cadastro.'
      );
    }
    if (identificador.length < 3) {
      return (
        'Nome de usuário curto',
        'O nome de usuário precisa ter pelo menos 3 caracteres.'
      );
    }
    if (senha.isEmpty) {
      return ('Senha obrigatória', 'Digite sua senha para continuar.');
    }
    return null;
  }

  (String, String) mensagemErroLogin(DioException erro) {
    final status = erro.response?.statusCode;
    final tipo = erro.type;

    if (status == 401 || status == 403) {
      return (
        'Nome de usuário ou senha não conferem',
        'Confira os dados digitados. Se ainda não tiver conta, toque em Criar conta.'
      );
    }
    if (status == 422) {
      return (
        'Revise os campos',
        'Alguma informação está incompleta ou em formato inválido.'
      );
    }
    if (status == 429) {
      return (
        'Muitas tentativas',
        'Aguarde um pouco antes de tentar novamente.'
      );
    }
    if (status != null && status >= 500) {
      return (
        'Servidor indisponível',
        'A API respondeu com erro. Tente novamente em alguns instantes.'
      );
    }
    if (tipo == DioExceptionType.connectionTimeout ||
        tipo == DioExceptionType.receiveTimeout ||
        tipo == DioExceptionType.sendTimeout) {
      return (
        'Conexão demorou demais',
        'Verifique sua internet e se o backend está ligado.'
      );
    }
    if (tipo == DioExceptionType.connectionError || erro.response == null) {
      return (
        'Sem conexão com a API',
        'Verifique sua internet, o Wi-Fi e se o endereço do backend está correto.'
      );
    }

    return ('Não foi possível entrar', 'Confira seus dados e tente novamente.');
  }

  Future<void> entrarComoConvidado() async {
    await tokenService.limparTokens();

    if (!mounted) return;
    Navigator.pushReplacementNamed(context, '/home');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Entrar')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Text(
              'Bebidas Scan',
              style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            TextField(
              controller: identificadorController,
              decoration: const InputDecoration(labelText: 'Nome de usuário'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: senhaController,
              decoration: const InputDecoration(labelText: 'Senha'),
              obscureText: true,
              onSubmitted: (_) => entrar(),
            ),
            if (erro != null) ...[
              const SizedBox(height: 12),
              _MensagemErroLogin(
                titulo: erroTitulo ?? 'Não foi possível entrar',
                mensagem: erro!,
              ),
            ],
            const SizedBox(height: 20),
            FilledButton(
              onPressed: carregando ? null : entrar,
              child: Text(carregando ? 'Entrando...' : 'Entrar'),
            ),
            const SizedBox(height: 8),
            OutlinedButton(
              onPressed: carregando ? null : entrarComoConvidado,
              child: const Text('Continuar sem conta'),
            ),
            TextButton(
              onPressed: () => Navigator.pushNamed(context, '/registrar'),
              child: const Text('Criar conta'),
            ),
            TextButton(
              onPressed: () => Navigator.pushNamed(context, '/recuperar-senha'),
              child: const Text('Esqueci minha senha'),
            ),
          ],
        ),
      ),
    );
  }
}

class _MensagemErroLogin extends StatelessWidget {
  const _MensagemErroLogin({
    required this.titulo,
    required this.mensagem,
  });

  final String titulo;
  final String mensagem;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return Semantics(
      liveRegion: true,
      label: '$titulo. $mensagem',
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: colors.errorContainer,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: colors.error),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.error_outline, color: colors.onErrorContainer),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    titulo,
                    style: TextStyle(
                      color: colors.onErrorContainer,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    mensagem,
                    style: TextStyle(color: colors.onErrorContainer),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

import 'package:dio/dio.dart';

import 'token_service.dart';

const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'https://api.bebidasscan.com.br',
);

class ApiService {
  ApiService()
      : dio = Dio(
          BaseOptions(
            baseUrl: apiBaseUrl,
            connectTimeout: const Duration(seconds: 10),
            receiveTimeout: const Duration(seconds: 20),
            headers: const {'User-Agent': 'BebidasScan/0.1'},
          ),
        ) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await tokenService.lerAccessToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          final status = error.response?.statusCode;
          final jaTentouRenovar =
              error.requestOptions.extra['tokenRetried'] == true;
          if (status == 401 &&
              !jaTentouRenovar &&
              !error.requestOptions.path.contains('/auth/')) {
            final refreshed = await _tentarRenovarAccessToken();
            if (refreshed) {
              final token = await tokenService.lerAccessToken();
              final options = error.requestOptions;
              options.headers['Authorization'] = 'Bearer $token';
              options.extra['tokenRetried'] = true;
              final retry = await dio.fetch(options);
              return handler.resolve(retry);
            }
          }
          handler.next(error);
        },
      ),
    );
  }

  final Dio dio;
  final TokenService tokenService = TokenService();

  Future<bool> _tentarRenovarAccessToken() async {
    final refreshToken = await tokenService.lerRefreshToken();
    if (refreshToken == null) return false;

    try {
      final response = await Dio(
        BaseOptions(
          baseUrl: apiBaseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 20),
          headers: const {'User-Agent': 'BebidasScan/0.1'},
        ),
      ).post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      await tokenService.salvarAccessToken(response.data['access_token']);
      return true;
    } catch (_) {
      await tokenService.limparTokens();
      return false;
    }
  }

  Future<Response> registrar({
    required String nome,
    required String nomeUsuario,
    required String email,
    required String senha,
    required String dataNascimento,
    required bool aceitouPrivacidade,
    required bool aceitouTermos,
    required bool marketingConsentimento,
  }) {
    return dio.post(
      '/auth/registrar',
      data: {
        'nome': nome,
        'nome_usuario': nomeUsuario,
        'email': email,
        'senha': senha,
        'data_nascimento': dataNascimento,
        'aceitou_privacidade': aceitouPrivacidade,
        'aceitou_termos': aceitouTermos,
        'marketing_consentimento': marketingConsentimento,
      },
    );
  }

  Future<Response> login({
    required String identificador,
    required String senha,
  }) {
    return dio.post(
      '/auth/login',
      data: {'identificador': identificador, 'senha': senha},
    );
  }

  Future<Response> logout() async {
    final refreshToken = await tokenService.lerRefreshToken();
    if (refreshToken == null) {
      return Response(requestOptions: RequestOptions(path: '/auth/logout'));
    }
    return dio.post('/auth/logout', data: {'refresh_token': refreshToken});
  }

  Future<Response> alterarSenha({
    required String senhaAtual,
    required String novaSenha,
  }) {
    return dio.post(
      '/auth/alterar-senha',
      data: {'senha_atual': senhaAtual, 'nova_senha': novaSenha},
    );
  }

  Future<Response> solicitarResetSenha(String email) {
    return dio.post('/auth/solicitar-reset-senha', data: {'email': email});
  }

  Future<Response> perfil() {
    return dio.get('/perfil/me');
  }

  Future<Response> statusLgpd() {
    return dio.get('/perfil/lgpd/status');
  }

  Future<Response> aceitarLgpd({
    required String dataNascimento,
    required bool aceitouPrivacidade,
    required bool aceitouTermos,
    required bool marketingConsentimento,
  }) {
    return dio.post(
      '/perfil/lgpd/aceitar',
      data: {
        'data_nascimento': dataNascimento,
        'aceitou_privacidade': aceitouPrivacidade,
        'aceitou_termos': aceitouTermos,
        'marketing_consentimento': marketingConsentimento,
      },
    );
  }

  Future<Response> politicaPrivacidade() {
    return dio.get('/privacidade/politica');
  }

  Future<Response> termosUso() {
    return dio.get('/privacidade/termos');
  }

  Future<Response> exportarDadosCsv(List<String> categorias) {
    return dio.get(
      '/perfil/exportar.csv',
      queryParameters: {'categorias': categorias.join(',')},
      options: Options(responseType: ResponseType.plain),
    );
  }

  Future<Response> anonimizarConta({
    required String email,
    required String senha,
  }) {
    return dio.post(
      '/perfil/anonimizar',
      data: {'email': email, 'senha': senha},
    );
  }

  Future<Response> buscarBebidaPorCodigo(String codigo) {
    return dio.get('/bebidas/codigo/$codigo');
  }

  Future<Response> buscarBebidaPorNome(String termo) {
    return dio.get('/bebidas/buscar', queryParameters: {'q': termo});
  }

  Future<Response> criarBebida(Map<String, dynamic> dados) {
    return dio.post('/bebidas', data: dados);
  }

  Future<Response> atualizarBebida(int idBebida, Map<String, dynamic> dados) {
    return dio.patch('/bebidas/$idBebida', data: dados);
  }

  Future<Response> avaliarBebida({
    required int idBebida,
    required int nota,
    String? comentario,
    bool? comprariaNovamente,
  }) {
    return dio.post(
      '/avaliacoes',
      data: {
        'id_bebida': idBebida,
        'nota': nota,
        'comentario': comentario,
        'compraria_novamente': comprariaNovamente,
      },
    );
  }

  Future<Response> favoritar(int idBebida) {
    return dio.post('/favoritos/$idBebida');
  }

  Future<Response> listarFavoritos() {
    return dio.get('/favoritos');
  }
}

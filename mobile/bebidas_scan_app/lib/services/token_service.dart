import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenService {
  static const _storage = FlutterSecureStorage();
  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';

  Future<void> salvarTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _storage.write(key: _accessKey, value: accessToken);
    await _storage.write(key: _refreshKey, value: refreshToken);
  }

  Future<String?> lerAccessToken() {
    return _storage.read(key: _accessKey);
  }

  Future<String?> lerRefreshToken() {
    return _storage.read(key: _refreshKey);
  }

  Future<void> salvarAccessToken(String accessToken) {
    return _storage.write(key: _accessKey, value: accessToken);
  }

  Future<void> limparTokens() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
  }
}

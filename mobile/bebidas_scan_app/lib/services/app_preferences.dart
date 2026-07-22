import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AppPreferences {
  static const _storage = FlutterSecureStorage();
  static const _onboardingKey = 'onboarding_concluido';
  static const _scannerVibracaoKey = 'scanner_vibracao';
  static const _scannerLanternaKey = 'scanner_lanterna_automatica';
  static const _scannerModoKey = 'scanner_modo';
  static const _guiaSonoroCameraKey = 'guia_sonoro_camera';
  static const _sugestaoAcessibilidadeKey = 'sugestao_acessibilidade_exibida';

  Future<bool> onboardingConcluido() async {
    return await _storage.read(key: _onboardingKey) == 'true';
  }

  Future<void> marcarOnboardingConcluido() {
    return _storage.write(key: _onboardingKey, value: 'true');
  }

  Future<bool> vibracaoScannerAtiva() async {
    return await _storage.read(key: _scannerVibracaoKey) != 'false';
  }

  Future<void> salvarVibracaoScanner(bool valor) {
    return _storage.write(key: _scannerVibracaoKey, value: valor.toString());
  }

  Future<bool> lanternaAutomaticaAtiva() async {
    return await _storage.read(key: _scannerLanternaKey) == 'true';
  }

  Future<void> salvarLanternaAutomatica(bool valor) {
    return _storage.write(key: _scannerLanternaKey, value: valor.toString());
  }

  Future<String> modoScanner() async {
    return await _storage.read(key: _scannerModoKey) ?? 'obturador';
  }

  Future<void> salvarModoScanner(String valor) {
    final modo = valor == 'automatico' ? 'automatico' : 'obturador';
    return _storage.write(key: _scannerModoKey, value: modo);
  }

  Future<bool> guiaSonoroCameraAtivo() async {
    return await _storage.read(key: _guiaSonoroCameraKey) == 'true';
  }

  Future<void> salvarGuiaSonoroCamera(bool valor) {
    return _storage.write(
      key: _guiaSonoroCameraKey,
      value: valor.toString(),
    );
  }

  Future<bool> sugestaoAcessibilidadeExibida() async {
    return await _storage.read(key: _sugestaoAcessibilidadeKey) == 'true';
  }

  Future<void> marcarSugestaoAcessibilidadeExibida() {
    return _storage.write(key: _sugestaoAcessibilidadeKey, value: 'true');
  }
}

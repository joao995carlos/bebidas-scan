import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/app_preferences.dart';
import '../services/permission_service.dart';

class SplashPage extends StatefulWidget {
  const SplashPage({super.key});

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> {
  final api = ApiService();
  final preferences = AppPreferences();
  final permissions = PermissionService();

  @override
  void initState() {
    super.initState();
    _verificarSessao();
  }

  Future<void> _verificarSessao() async {
    final onboardingConcluido = await preferences.onboardingConcluido();
    if (!mounted) return;
    if (!onboardingConcluido) {
      Navigator.pushReplacementNamed(context, '/onboarding');
      return;
    }

    await permissions.requestStartupPermissions();
    if (!mounted) return;

    try {
      await api.perfil();
      final status = await api.statusLgpd();
      if (!mounted) return;
      final pendente = status.data['pendente'] == true;
      Navigator.pushReplacementNamed(
        context,
        pendente ? '/lgpd-aceitar' : '/home',
      );
    } catch (_) {
      if (!mounted) return;
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: CircularProgressIndicator()),
    );
  }
}

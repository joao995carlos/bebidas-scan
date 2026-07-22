import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'pages/bebida_form_page.dart';
import 'pages/bebida_page.dart';
import 'pages/bottle_ocr_page.dart';
import 'pages/change_password_page.dart';
import 'pages/forgot_password_page.dart';
import 'pages/home_page.dart';
import 'pages/lgpd_accept_page.dart';
import 'pages/login_page.dart';
import 'pages/onboarding_page.dart';
import 'pages/profile_page.dart';
import 'pages/privacy_document_page.dart';
import 'pages/privacy_page.dart';
import 'pages/register_page.dart';
import 'pages/scanner_page.dart';
import 'pages/splash_page.dart';
import 'services/app_preferences.dart';
import 'widgets/api_status_banner.dart';

void main() {
  runApp(const BebidasScanApp());
}

class BebidasScanApp extends StatelessWidget {
  const BebidasScanApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Bebidas Scan',
      debugShowCheckedModeBanner: false,
      locale: const Locale('pt', 'BR'),
      supportedLocales: const [
        Locale('pt', 'BR'),
      ],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ],
      builder: (context, child) {
        return AccessibilityPromptGate(
          child: ApiStatusBanner(child: child ?? const SizedBox.shrink()),
        );
      },
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xff1f7a5c),
          primary: const Color(0xff1f7a5c),
          secondary: const Color(0xffb45f2a),
          tertiary: const Color(0xff7a2434),
          surface: const Color(0xfffffbf5),
        ),
        scaffoldBackgroundColor: const Color(0xfffff4e8),
        useMaterial3: true,
        appBarTheme: const AppBarTheme(
          centerTitle: false,
          backgroundColor: Color(0xfffff4e8),
          foregroundColor: Color(0xff241611),
          surfaceTintColor: Colors.transparent,
        ),
        cardTheme: CardThemeData(
          color: const Color(0xfffffbf5),
          elevation: 0,
          shape: RoundedRectangleBorder(
            side: const BorderSide(color: Color(0xffead8c6)),
            borderRadius: BorderRadius.circular(8),
          ),
        ),
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
          filled: true,
          fillColor: Color(0xffffffff),
        ),
        navigationBarTheme: NavigationBarThemeData(
          backgroundColor: const Color(0xfffffbf5),
          indicatorColor: const Color(0xfff3b35f),
          labelTextStyle: WidgetStateProperty.all(
            const TextStyle(fontWeight: FontWeight.w700),
          ),
        ),
        chipTheme: ChipThemeData(
          backgroundColor: const Color(0xfffffbf5),
          selectedColor: const Color(0xfff3b35f),
          side: const BorderSide(color: Color(0xffead8c6)),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: const Color(0xff1f7a5c),
            foregroundColor: Colors.white,
            minimumSize: const Size(48, 48),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: const Color(0xff7a2434),
            side: const BorderSide(color: Color(0xffb45f2a)),
            minimumSize: const Size(48, 48),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        ),
        snackBarTheme: const SnackBarThemeData(
          behavior: SnackBarBehavior.floating,
          backgroundColor: Color(0xff241611),
          contentTextStyle: TextStyle(color: Colors.white),
        ),
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => const SplashPage(),
        '/onboarding': (context) => const OnboardingPage(),
        '/login': (context) => const LoginPage(),
        '/recuperar-senha': (context) => const ForgotPasswordPage(),
        '/alterar-senha': (context) => const ChangePasswordPage(),
        '/registrar': (context) => const RegisterPage(),
        '/lgpd-aceitar': (context) => const LgpdAcceptPage(),
        '/documento-privacidade': (context) => const PrivacyDocumentPage(),
        '/privacidade': (context) => const PrivacyPage(),
        '/perfil': (context) => const ProfilePage(),
        '/home': (context) => const HomePage(),
        '/scanner': (context) => const ScannerPage(),
        '/bottle-ocr': (context) => const BottleOcrPage(),
        '/bebida': (context) => const BebidaPage(),
        '/bebida-form': (context) => const BebidaFormPage(),
      },
    );
  }
}

class AccessibilityPromptGate extends StatefulWidget {
  const AccessibilityPromptGate({super.key, required this.child});

  final Widget child;

  @override
  State<AccessibilityPromptGate> createState() =>
      _AccessibilityPromptGateState();
}

class _AccessibilityPromptGateState extends State<AccessibilityPromptGate> {
  final preferences = AppPreferences();
  bool verificando = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    verificarAcessibilidade();
  }

  Future<void> verificarAcessibilidade() async {
    if (verificando) return;

    final mediaQuery = MediaQuery.maybeOf(context);
    final acessibilidadeAtiva = mediaQuery?.accessibleNavigation == true ||
        WidgetsBinding.instance.platformDispatcher.accessibilityFeatures
            .accessibleNavigation;

    if (!acessibilidadeAtiva) return;

    verificando = true;
    final jaExibiu = await preferences.sugestaoAcessibilidadeExibida();
    final guiaAtivo = await preferences.guiaSonoroCameraAtivo();
    if (!mounted || jaExibiu || guiaAtivo) return;

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        mostrarDialogoAcessibilidade();
      }
    });
  }

  Future<void> mostrarDialogoAcessibilidade() async {
    final ativar = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text('Recursos de acessibilidade'),
        content: const Text(
          'Detectamos que um recurso de acessibilidade pode estar ativo no '
          'Android. Deseja ativar automaticamente funções para facilitar o uso?\n\n'
          '- Guia sonoro de câmera no scanner\n'
          '- Vibração curta ao detectar código\n'
          '- Detecção automática de código de barras',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Agora não'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Ativar'),
          ),
        ],
      ),
    );

    await preferences.marcarSugestaoAcessibilidadeExibida();
    if (ativar == true) {
      await preferences.salvarGuiaSonoroCamera(true);
      await preferences.salvarVibracaoScanner(true);
      await preferences.salvarModoScanner('automatico');
    }
  }

  @override
  Widget build(BuildContext context) => widget.child;
}

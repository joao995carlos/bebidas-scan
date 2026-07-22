import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../services/api_service.dart';

class ApiStatusBanner extends StatefulWidget {
  const ApiStatusBanner({super.key, required this.child});

  final Widget child;

  @override
  State<ApiStatusBanner> createState() => _ApiStatusBannerState();
}

class _ApiStatusBannerState extends State<ApiStatusBanner>
    with WidgetsBindingObserver {
  Timer? timer;
  bool offline = false;
  bool verificando = false;
  DateTime? ultimaFalha;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    verificarAgora();
    timer =
        Timer.periodic(const Duration(seconds: 15), (_) => verificarAgora());
  }

  @override
  void dispose() {
    timer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      verificarAgora();
    }
  }

  Future<void> verificarAgora() async {
    if (verificando) return;
    verificando = true;
    try {
      final dio = Dio(
        BaseOptions(
          baseUrl: apiBaseUrl,
          connectTimeout: const Duration(seconds: 4),
          receiveTimeout: const Duration(seconds: 4),
          headers: const {'User-Agent': 'BebidasScan/0.1'},
        ),
      );
      final resposta = await dio.get('/health');
      final ok = resposta.statusCode == 200;
      if (!mounted) return;
      setState(() {
        offline = !ok;
        if (!ok) ultimaFalha = DateTime.now();
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        offline = true;
        ultimaFalha = DateTime.now();
      });
    } finally {
      verificando = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.viewPaddingOf(context).bottom;

    return Stack(
      children: [
        widget.child,
        Positioned(
          left: 0,
          right: 0,
          bottom: 0,
          child: IgnorePointer(
            ignoring: !offline,
            child: AnimatedSlide(
              offset: offline ? Offset.zero : const Offset(0, 1),
              duration: const Duration(milliseconds: 220),
              curve: Curves.easeOut,
              child: AnimatedOpacity(
                opacity: offline ? 1 : 0,
                duration: const Duration(milliseconds: 180),
                child: _OfflineBar(
                  bottomInset: bottomInset,
                  ultimaFalha: ultimaFalha,
                  onRetry: verificarAgora,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _OfflineBar extends StatelessWidget {
  const _OfflineBar({
    required this.bottomInset,
    required this.ultimaFalha,
    required this.onRetry,
  });

  final double bottomInset;
  final DateTime? ultimaFalha;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final hora = ultimaFalha == null
        ? ''
        : ' ${ultimaFalha!.hour.toString().padLeft(2, '0')}:${ultimaFalha!.minute.toString().padLeft(2, '0')}';

    return Material(
      color: const Color(0xff8f1d2c),
      elevation: 8,
      child: SafeArea(
        top: false,
        child: Padding(
          padding: EdgeInsets.fromLTRB(14, 10, 8, bottomInset > 0 ? 4 : 10),
          child: Row(
            children: [
              const Icon(Icons.cloud_off, color: Colors.white),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Backend offline$hora. Verifique se a API está ligada.',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              TextButton(
                onPressed: onRetry,
                style: TextButton.styleFrom(foregroundColor: Colors.white),
                child: const Text('Testar'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';

import '../services/app_preferences.dart';

class OnboardingPage extends StatefulWidget {
  const OnboardingPage({super.key});

  @override
  State<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends State<OnboardingPage> {
  final controller = PageController();
  final preferences = AppPreferences();
  int pagina = 0;

  final slides = const [
    _SlideData(
      icon: Icons.qr_code_scanner,
      title: 'Escaneie bebidas',
      text:
          'Aponte a câmera para o código de barras e encontre dados da bebida em poucos segundos.',
      color: Color(0xff1f7a5c),
      accent: Color(0xfff3b35f),
    ),
    _SlideData(
      icon: Icons.local_bar_outlined,
      title: 'Complete o rótulo',
      text:
          'Quando faltar algo, cadastre tipo, marca, origem, teor alcoólico e detalhes da cachaça.',
      color: Color(0xff7a2434),
      accent: Color(0xff59b08c),
    ),
    _SlideData(
      icon: Icons.star_border,
      title: 'Monte sua lista',
      text:
          'Salve favoritos, registre avaliações e encontre bebidas boas para comprar de novo.',
      color: Color(0xffb45f2a),
      accent: Color(0xff273f73),
    ),
    _SlideData(
      icon: Icons.privacy_tip_outlined,
      title: 'Privacidade no perfil',
      text:
          'No Perfil ficam configurações, documentos LGPD, exportação CSV e exclusão de conta.',
      color: Color(0xff273f73),
      accent: Color(0xffd79a3b),
    ),
  ];

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  Future<void> fechar() async {
    await preferences.marcarOnboardingConcluido();
    if (!mounted) return;
    if (Navigator.canPop(context)) {
      Navigator.pop(context);
      return;
    }
    Navigator.pushReplacementNamed(context, '/');
  }

  void anterior() {
    if (pagina == 0) return;
    controller.previousPage(
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeOut,
    );
  }

  void proximo() {
    if (pagina == slides.length - 1) {
      fechar();
      return;
    }
    controller.nextPage(
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeOut,
    );
  }

  @override
  Widget build(BuildContext context) {
    final slideAtual = slides[pagina];
    final ultimo = pagina == slides.length - 1;

    return Scaffold(
      backgroundColor: const Color(0xfffff4e8),
      body: SafeArea(
        child: Stack(
          children: [
            Positioned(
              top: 0,
              left: 0,
              right: 0,
              height: 188,
              child: ColoredBox(color: slideAtual.color),
            ),
            Positioned(
              top: 132,
              left: 24,
              right: 24,
              child: Container(
                height: 70,
                decoration: BoxDecoration(
                  color: slideAtual.accent,
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
            PageView.builder(
              controller: controller,
              itemCount: slides.length,
              onPageChanged: (valor) => setState(() => pagina = valor),
              itemBuilder: (context, index) {
                final slide = slides[index];
                return Padding(
                  padding: const EdgeInsets.fromLTRB(24, 52, 24, 112),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Bebidas Scan',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w800,
                          fontSize: 30,
                          height: 1,
                        ),
                      ),
                      const SizedBox(height: 44),
                      Expanded(
                        child: Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(24),
                          decoration: BoxDecoration(
                            color: const Color(0xfffffbf5),
                            border: Border.all(color: const Color(0xffead8c6)),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Container(
                                width: 128,
                                height: 128,
                                decoration: BoxDecoration(
                                  color: slide.accent.withValues(alpha: .22),
                                  border: Border.all(
                                    color: slide.accent,
                                    width: 2,
                                  ),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Icon(
                                  slide.icon,
                                  size: 64,
                                  color: slide.color,
                                ),
                              ),
                              const SizedBox(height: 28),
                              Text(
                                slide.title,
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: slide.color,
                                  fontSize: 30,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              const SizedBox(height: 14),
                              Text(
                                slide.text,
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                  fontSize: 17,
                                  height: 1.45,
                                  color: Color(0xff4e4038),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
            Positioned(
              top: 8,
              right: 8,
              child: IconButton(
                tooltip: 'Fechar guia',
                onPressed: fechar,
                color: Colors.white,
                icon: const Icon(Icons.close),
              ),
            ),
            Positioned(
              left: 24,
              right: 24,
              bottom: 24,
              child: Row(
                children: [
                  OutlinedButton.icon(
                    onPressed: pagina == 0 ? null : anterior,
                    icon: const Icon(Icons.chevron_left),
                    label: const Text('Anterior'),
                  ),
                  const Spacer(),
                  Row(
                    children: [
                      for (var index = 0; index < slides.length; index++)
                        Container(
                          width: index == pagina ? 22 : 8,
                          height: 8,
                          margin: const EdgeInsets.symmetric(horizontal: 3),
                          decoration: BoxDecoration(
                            color: index == pagina
                                ? slideAtual.color
                                : const Color(0xffd8c7b5),
                            borderRadius: BorderRadius.circular(99),
                          ),
                        ),
                    ],
                  ),
                  const Spacer(),
                  FilledButton.icon(
                    onPressed: proximo,
                    icon: Icon(ultimo ? Icons.check : Icons.chevron_right),
                    label: Text(ultimo ? 'Começar' : 'Próximo'),
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

class _SlideData {
  const _SlideData({
    required this.icon,
    required this.title,
    required this.text,
    required this.color,
    required this.accent,
  });

  final IconData icon;
  final String title;
  final String text;
  final Color color;
  final Color accent;
}

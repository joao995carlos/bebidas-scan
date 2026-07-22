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
      preview: _PreviewKind.scanner,
      title: 'Escaneie bebidas',
      text:
          'Use a câmera, a moldura de alinhamento e o guia sonoro para encontrar o código com mais segurança.',
      color: Color(0xff1f7a5c),
      accent: Color(0xfff3b35f),
    ),
    _SlideData(
      preview: _PreviewKind.home,
      title: 'Pesquise mais rápido',
      text:
          'A tela inicial destaca busca, sugestões, histórico e atalhos para as ações principais.',
      color: Color(0xff7a2434),
      accent: Color(0xff59b08c),
    ),
    _SlideData(
      preview: _PreviewKind.bebida,
      title: 'Confira os dados',
      text:
          'Veja imagem, marca, origem Brasil, ingredientes e informações externas em uma tela organizada.',
      color: Color(0xffb45f2a),
      accent: Color(0xff273f73),
    ),
    _SlideData(
      preview: _PreviewKind.perfil,
      title: 'Controle sua conta',
      text:
          'Perfil reúne privacidade, LGPD, configurações do scanner, acessibilidade e permissões.',
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
                          padding: const EdgeInsets.fromLTRB(18, 18, 18, 20),
                          decoration: BoxDecoration(
                            color: const Color(0xfffffbf5),
                            border: Border.all(color: const Color(0xffead8c6)),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Column(
                            children: [
                              Expanded(
                                child: _AppPreview(
                                  kind: slide.preview,
                                  color: slide.color,
                                  accent: slide.accent,
                                ),
                              ),
                              const SizedBox(height: 18),
                              Text(
                                slide.title,
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: slide.color,
                                  fontSize: 27,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              const SizedBox(height: 10),
                              Text(
                                slide.text,
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                  fontSize: 16,
                                  height: 1.35,
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

class _AppPreview extends StatelessWidget {
  const _AppPreview({
    required this.kind,
    required this.color,
    required this.accent,
  });

  final _PreviewKind kind;
  final Color color;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: .72,
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: const Color(0xff241611),
          borderRadius: BorderRadius.circular(22),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: .18),
              blurRadius: 18,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(14),
          child: DecoratedBox(
            decoration: const BoxDecoration(color: Color(0xfffff4e8)),
            child: switch (kind) {
              _PreviewKind.scanner => _ScannerPreview(accent: accent),
              _PreviewKind.home => _HomePreview(color: color, accent: accent),
              _PreviewKind.bebida =>
                _BebidaPreview(color: color, accent: accent),
              _PreviewKind.perfil => _ProfilePreview(color: color),
            },
          ),
        ),
      ),
    );
  }
}

class _ScannerPreview extends StatelessWidget {
  const _ScannerPreview({required this.accent});

  final Color accent;

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        const DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xff151515), Color(0xff303030)],
            ),
          ),
        ),
        Center(
          child: Container(
            width: 160,
            height: 96,
            decoration: BoxDecoration(
              border: Border.all(color: accent, width: 3),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Center(
              child: Container(height: 2, width: 122, color: accent),
            ),
          ),
        ),
        Positioned(
          left: 12,
          right: 12,
          bottom: 12,
          child: Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: const Color(0xff241611).withValues(alpha: .9),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: accent),
            ),
            child: Row(
              children: [
                Icon(Icons.center_focus_strong, size: 20, color: accent),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'Centralize para confirmar',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _HomePreview extends StatelessWidget {
  const _HomePreview({required this.color, required this.accent});

  final Color color;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const _PreviewLine(width: 120, color: Colors.white, height: 12),
                const SizedBox(height: 8),
                _PreviewLine(width: 170, color: accent, height: 8),
                const SizedBox(height: 12),
                _PreviewButton(label: 'Escanear', color: accent),
              ],
            ),
          ),
          const SizedBox(height: 12),
          const _PreviewSearch(),
          const SizedBox(height: 10),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: const [
              _PreviewChip(label: 'coca'),
              _PreviewChip(label: 'água'),
              _PreviewChip(label: 'suco'),
            ],
          ),
          const SizedBox(height: 12),
          const _PreviewProductCard(
              title: 'Coca Cola Zero', subtitle: 'Brasil'),
        ],
      ),
    );
  }
}

class _BebidaPreview extends StatelessWidget {
  const _BebidaPreview({required this.color, required this.accent});

  final Color color;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Container(
                  width: 48,
                  height: 68,
                  decoration: BoxDecoration(
                    color: const Color(0xfffffbf5),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.local_drink_outlined, color: color),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const _PreviewLine(
                          width: 118, color: Colors.white, height: 11),
                      const SizedBox(height: 7),
                      _PreviewLine(width: 78, color: accent, height: 8),
                      const SizedBox(height: 8),
                      const _PreviewChip(label: 'Brasil'),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
          const _PreviewSection(title: 'Informações'),
          const SizedBox(height: 8),
          const _PreviewSection(title: 'Ingredientes'),
          const SizedBox(height: 8),
          const _PreviewSection(title: 'Minha avaliação'),
        ],
      ),
    );
  }
}

class _ProfilePreview extends StatelessWidget {
  const _ProfilePreview({required this.color});

  final Color color;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _PreviewLine(width: 86, color: color, height: 14),
          const SizedBox(height: 12),
          const _PreviewSection(title: 'Conta'),
          const SizedBox(height: 8),
          const _PreviewSection(title: 'Privacidade e LGPD'),
          const SizedBox(height: 8),
          const _PreviewSection(title: 'Configurações'),
          const SizedBox(height: 8),
          Row(
            children: [
              Icon(Icons.hearing, size: 20, color: color),
              const SizedBox(width: 8),
              const Expanded(
                  child: _PreviewLine(
                      width: 110, color: Color(0xff8a786b), height: 9)),
              Switch(value: true, onChanged: null),
            ],
          ),
        ],
      ),
    );
  }
}

class _PreviewProductCard extends StatelessWidget {
  const _PreviewProductCard({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xfffffbf5),
        border: Border.all(color: const Color(0xffead8c6)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: const Color(0xff1f7a5c).withValues(alpha: .14),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.local_drink_outlined, size: 22),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                        fontSize: 11, fontWeight: FontWeight.bold)),
                Text(subtitle,
                    style: const TextStyle(
                        fontSize: 10, color: Color(0xff6e5f55))),
              ],
            ),
          ),
          const Icon(Icons.chevron_right, size: 18),
        ],
      ),
    );
  }
}

class _PreviewSection extends StatelessWidget {
  const _PreviewSection({required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xfffffbf5),
        border: Border.all(color: const Color(0xffead8c6)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style:
                  const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          const _PreviewLine(width: 150, color: Color(0xffc9b7a4), height: 7),
          const SizedBox(height: 5),
          const _PreviewLine(width: 112, color: Color(0xffd8c7b5), height: 7),
        ],
      ),
    );
  }
}

class _PreviewSearch extends StatelessWidget {
  const _PreviewSearch();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 38,
      padding: const EdgeInsets.symmetric(horizontal: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: const Color(0xffead8c6)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: const Row(
        children: [
          Icon(Icons.search, size: 18, color: Color(0xff6e5f55)),
          SizedBox(width: 8),
          Expanded(
              child: _PreviewLine(
                  width: 130, color: Color(0xffc9b7a4), height: 8)),
        ],
      ),
    );
  }
}

class _PreviewButton extends StatelessWidget {
  const _PreviewButton({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 32,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.bold,
          color: Color(0xff241611),
        ),
      ),
    );
  }
}

class _PreviewChip extends StatelessWidget {
  const _PreviewChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xffead8c6),
        borderRadius: BorderRadius.circular(99),
      ),
      child: Text(label, style: const TextStyle(fontSize: 10)),
    );
  }
}

class _PreviewLine extends StatelessWidget {
  const _PreviewLine({
    required this.width,
    required this.color,
    required this.height,
  });

  final double width;
  final Color color;
  final double height;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(99),
        ),
      ),
    );
  }
}

class _SlideData {
  const _SlideData({
    required this.preview,
    required this.title,
    required this.text,
    required this.color,
    required this.accent,
  });

  final _PreviewKind preview;
  final String title;
  final String text;
  final Color color;
  final Color accent;
}

enum _PreviewKind { scanner, home, bebida, perfil }

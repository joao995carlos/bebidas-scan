import 'dart:io';

import 'package:camera/camera.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../services/api_service.dart';
import '../services/app_preferences.dart';

class ScannerPage extends StatefulWidget {
  const ScannerPage({super.key});

  @override
  State<ScannerPage> createState() => _ScannerPageState();
}

class _ScannerPageState extends State<ScannerPage> with WidgetsBindingObserver {
  static const leitorNativo = MethodChannel('bebidas_scan/native_barcode');

  final api = ApiService();
  final preferences = AppPreferences();
  final codigoController = TextEditingController();

  CameraController? cameraController;
  bool cameraInicializando = true;
  String? cameraErro;
  bool lendo = false;
  bool lanternaLigada = false;
  bool encerrando = false;
  bool vibracaoAtiva = true;
  bool lanternaAutomatica = false;
  bool deteccaoAutomatica = false;
  bool guiaSonoroCamera = false;
  int autoToken = 0;
  String statusLeitura = 'Aponte para o código e toque em ler código.';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    carregarPreferenciasEInicializar();
  }

  @override
  void dispose() {
    encerrando = true;
    autoToken++;
    WidgetsBinding.instance.removeObserver(this);
    codigoController.dispose();
    encerrarCamera();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.inactive ||
        state == AppLifecycleState.paused) {
      autoToken++;
      encerrarCamera();
      return;
    }

    if (state == AppLifecycleState.resumed && !encerrando) {
      carregarPreferenciasEInicializar();
    }
  }

  Future<void> carregarPreferenciasEInicializar() async {
    final vibracao = await preferences.vibracaoScannerAtiva();
    final flash = await preferences.lanternaAutomaticaAtiva();
    final guiaSonoro = await preferences.guiaSonoroCameraAtivo();
    final modo = await preferences.modoScanner();
    if (!mounted || encerrando) return;
    setState(() {
      vibracaoAtiva = vibracao;
      lanternaAutomatica = flash;
      guiaSonoroCamera = guiaSonoro;
      deteccaoAutomatica = modo == 'automatico';
    });
    await inicializarCamera();
  }

  String statusInicial() {
    return deteccaoAutomatica
        ? 'Aponte para o código. A leitura automática está ativa.'
        : 'Aponte para o código e toque em ler código.';
  }

  Future<void> inicializarCamera() async {
    setState(() {
      cameraInicializando = true;
      cameraErro = null;
      statusLeitura = statusInicial();
    });

    try {
      final cameras = await availableCameras();
      final camera = selecionarCameraTraseira(cameras);
      if (camera == null) {
        throw CameraException(
            'no_camera', 'Nenhuma câmera traseira encontrada.');
      }

      final controller = CameraController(
        camera,
        ResolutionPreset.high,
        enableAudio: false,
      );

      await controller.initialize();
      await controller.lockCaptureOrientation(DeviceOrientation.portraitUp);
      await controller.setFocusMode(FocusMode.auto);
      await controller.setFlashMode(
        lanternaAutomatica ? FlashMode.torch : FlashMode.off,
      );

      if (!mounted || encerrando) {
        await controller.dispose();
        return;
      }

      setState(() {
        cameraController = controller;
        cameraInicializando = false;
        lanternaLigada = lanternaAutomatica;
      });

      if (deteccaoAutomatica) {
        iniciarDeteccaoAutomatica();
      }
    } on CameraException catch (erro) {
      if (!mounted) return;
      setState(() {
        cameraErro = erro.description ?? erro.code;
        cameraInicializando = false;
      });
    } catch (erro) {
      if (!mounted) return;
      setState(() {
        cameraErro = erro.toString();
        cameraInicializando = false;
      });
    }
  }

  CameraDescription? selecionarCameraTraseira(List<CameraDescription> cameras) {
    final traseiras = cameras
        .where((camera) => camera.lensDirection == CameraLensDirection.back)
        .toList();
    if (traseiras.isEmpty) return null;

    final normais = traseiras.where((camera) {
      final nome = camera.name.toLowerCase();
      return !nome.contains('ultra') &&
          !nome.contains('wide') &&
          !nome.contains('tele');
    }).toList();

    return normais.isNotEmpty ? normais.first : traseiras.first;
  }

  Future<void> encerrarCamera() async {
    final controller = cameraController;
    cameraController = null;
    if (controller == null) return;

    await controller.dispose();
  }

  void iniciarDeteccaoAutomatica() {
    final token = ++autoToken;
    agendarLeituraAutomatica(token);
  }

  Future<void> agendarLeituraAutomatica(int token) async {
    await Future<void>.delayed(const Duration(milliseconds: 1300));
    if (!mounted ||
        encerrando ||
        token != autoToken ||
        !deteccaoAutomatica ||
        lendo) {
      if (mounted && !encerrando && token == autoToken && deteccaoAutomatica) {
        agendarLeituraAutomatica(token);
      }
      return;
    }

    await capturarELerCodigo(automatico: true);
    if (mounted &&
        !encerrando &&
        token == autoToken &&
        deteccaoAutomatica &&
        !lendo) {
      agendarLeituraAutomatica(token);
    }
  }

  Future<void> tocarGuiaSonoro({required bool detectou}) async {
    if (!guiaSonoroCamera) return;

    await SystemSound.play(
      detectou ? SystemSoundType.alert : SystemSoundType.click,
    );
  }

  Future<void> tocarGuiaSonoroAlinhamento(double alinhamento) async {
    if (!guiaSonoroCamera) return;

    final repeticoes = alinhamento >= 0.72 ? 3 : (alinhamento >= 0.48 ? 2 : 1);
    for (var i = 0; i < repeticoes; i++) {
      await SystemSound.play(SystemSoundType.click);
      if (i < repeticoes - 1) {
        await Future<void>.delayed(const Duration(milliseconds: 120));
      }
    }
  }

  double? numero(Map<String, dynamic> dados, String chave) {
    final valor = dados[chave];
    if (valor is num) return valor.toDouble();
    return double.tryParse(valor?.toString() ?? '');
  }

  String? codigoDetectado(Map<String, dynamic>? dados) {
    final codigo = dados?['code']?.toString().trim();
    return codigo == null || codigo.isEmpty ? null : codigo;
  }

  double alinhamentoDoCodigo(Map<String, dynamic> dados) {
    final largura = numero(dados, 'imageWidth');
    final altura = numero(dados, 'imageHeight');
    final centroX = numero(dados, 'centerX');
    final centroY = numero(dados, 'centerY');

    if (largura == null ||
        altura == null ||
        centroX == null ||
        centroY == null ||
        largura <= 0 ||
        altura <= 0) {
      return 1;
    }

    final deslocamentoX = ((centroX - largura / 2).abs() / (largura / 2));
    final deslocamentoY = ((centroY - altura / 2).abs() / (altura / 2));
    final deslocamento =
        deslocamentoX > deslocamentoY ? deslocamentoX : deslocamentoY;

    return (1 - deslocamento).clamp(0, 1).toDouble();
  }

  String instrucaoAlinhamento(Map<String, dynamic> dados) {
    final largura = numero(dados, 'imageWidth');
    final altura = numero(dados, 'imageHeight');
    final centroX = numero(dados, 'centerX');
    final centroY = numero(dados, 'centerY');

    if (largura == null ||
        altura == null ||
        centroX == null ||
        centroY == null) {
      return 'Código detectado. Mantenha o rótulo estável.';
    }

    final moverHorizontal = centroX < largura * 0.42
        ? 'Mova um pouco para a esquerda.'
        : (centroX > largura * 0.58 ? 'Mova um pouco para a direita.' : '');
    final moverVertical = centroY < altura * 0.42
        ? 'Desça um pouco o aparelho.'
        : (centroY > altura * 0.58 ? 'Suba um pouco o aparelho.' : '');

    return [
      'Código detectado. Centralize para confirmar.',
      moverHorizontal,
      moverVertical,
    ].where((parte) => parte.isNotEmpty).join(' ');
  }

  Future<void> alternarLanterna() async {
    final controller = cameraController;
    if (controller == null || !controller.value.isInitialized) return;

    try {
      final novoModo = lanternaLigada ? FlashMode.off : FlashMode.torch;
      await controller.setFlashMode(novoModo);
      if (!mounted) return;
      setState(() => lanternaLigada = !lanternaLigada);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Lanterna indisponível nesta câmera.')),
      );
    }
  }

  Future<void> capturarELerCodigo({bool automatico = false}) async {
    final controller = cameraController;
    if (controller == null || !controller.value.isInitialized || lendo) return;

    setState(() {
      lendo = true;
      statusLeitura =
          automatico ? 'Procurando código...' : 'Capturando imagem...';
    });

    XFile? foto;
    try {
      foto = await controller.takePicture();

      if (!mounted) return;
      setState(() => statusLeitura = 'Analisando código...');

      final dadosCodigo = await leitorNativo.invokeMapMethod<String, dynamic>(
        'scanImageInfoFile',
        {'path': foto.path},
      );
      final codigo = codigoDetectado(dadosCodigo);

      if (codigo == null) {
        if (!mounted) return;
        setState(() {
          lendo = false;
          statusLeitura = automatico
              ? 'Nenhum código detectado ainda. Mantenha o rótulo no quadro.'
              : 'Código não detectado. Aproxime, foque melhor e tente novamente.';
        });
        if (automatico) {
          await tocarGuiaSonoro(detectou: false);
        }
        return;
      }

      if (automatico && guiaSonoroCamera && dadosCodigo != null) {
        final alinhamento = alinhamentoDoCodigo(dadosCodigo);
        if (alinhamento < 0.70) {
          if (!mounted) return;
          setState(() {
            lendo = false;
            statusLeitura = instrucaoAlinhamento(dadosCodigo);
          });
          await tocarGuiaSonoroAlinhamento(alinhamento);
          return;
        }
      }

      await tocarGuiaSonoro(detectou: true);
      if (vibracaoAtiva) {
        await HapticFeedback.mediumImpact();
      }

      if (!mounted) return;
      setState(() => statusLeitura = 'Código detectado: $codigo');
      await buscarProduto(codigo);
    } catch (erro) {
      if (!mounted) return;
      setState(() {
        lendo = false;
        statusLeitura = 'Erro ao ler código: $erro';
      });
    } finally {
      if (foto != null) {
        try {
          await File(foto.path).delete();
        } catch (_) {
          // Arquivo temporário pode já ter sido limpo pelo sistema.
        }
      }
    }
  }

  Future<void> buscarProduto(String codigo) async {
    if (!lendo) setState(() => lendo = true);

    try {
      final resposta = await api.buscarBebidaPorCodigo(codigo);

      if (!mounted) return;
      Navigator.pushReplacementNamed(
        context,
        '/bebida',
        arguments: Map<String, dynamic>.from(resposta.data),
      );
    } on DioException catch (erro) {
      if (!mounted) return;
      final status = erro.response?.statusCode;
      if (status == 404) {
        await perguntarCadastro(codigo);
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Bebida não encontrada. Tente novamente.'),
        ),
      );
      setState(() {
        lendo = false;
        statusLeitura = 'Bebida não encontrada. Tente outro código.';
      });
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Não foi possível buscar a bebida.')),
      );
      setState(() {
        lendo = false;
        statusLeitura = 'Não foi possível buscar a bebida. Tente novamente.';
      });
    }
  }

  Future<void> perguntarCadastro(String codigo) async {
    setState(() {
      lendo = false;
      statusLeitura = 'Bebida não encontrada.';
    });

    final acao = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Bebida não encontrada'),
        content: const Text(
          'Você pode cadastrar manualmente ou tentar ler os dados do rótulo pela câmera.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, 'cancelar'),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, 'manual'),
            child: const Text('Cadastrar manualmente'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, 'ocr'),
            child: const Text('Ler dados da garrafa'),
          ),
        ],
      ),
    );

    if (!mounted) return;
    if (acao == 'ocr') {
      Navigator.pushReplacementNamed(
        context,
        '/bottle-ocr',
        arguments: {'codigo_barras': codigo},
      );
      return;
    }
    if (acao == 'manual') {
      Navigator.pushReplacementNamed(
        context,
        '/bebida-form',
        arguments: {'codigo_barras': codigo},
      );
    }
  }

  void buscarCodigoDigitado() {
    final codigo = codigoController.text.trim();
    if (codigo.isEmpty) return;
    buscarProduto(codigo);
  }

  @override
  Widget build(BuildContext context) {
    final modoTexto = deteccaoAutomatica ? 'Automático' : 'Obturador';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Escanear código de barras'),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: Center(child: Text(modoTexto)),
          ),
          IconButton(
            tooltip: lanternaLigada ? 'Desligar lanterna' : 'Ligar lanterna',
            onPressed: alternarLanterna,
            icon: Icon(
              lanternaLigada ? Icons.flashlight_off : Icons.flashlight_on,
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(
              statusLeitura,
              style: const TextStyle(fontSize: 18),
            ),
          ),
          Expanded(
            child: Semantics(
              label: 'Área da câmera para escanear código de barras',
              child: _CameraArea(
                controller: cameraController,
                inicializando: cameraInicializando,
                erro: cameraErro,
                status: statusLeitura,
                automatico: deteccaoAutomatica,
                lendo: lendo,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: FilledButton.icon(
              onPressed: lendo || deteccaoAutomatica
                  ? null
                  : () => capturarELerCodigo(),
              icon: Icon(
                deteccaoAutomatica
                    ? Icons.center_focus_strong
                    : Icons.document_scanner,
              ),
              label: Text(
                deteccaoAutomatica
                    ? 'Detecção automática ativa'
                    : (lendo ? 'Lendo...' : 'Ler código'),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: codigoController,
                    decoration: const InputDecoration(
                      labelText: 'Código de barras',
                      hintText: 'Digite se a câmera não ler',
                    ),
                    keyboardType: TextInputType.number,
                    onSubmitted: (_) => buscarCodigoDigitado(),
                  ),
                ),
                const SizedBox(width: 8),
                FilledButton(
                  onPressed: lendo ? null : buscarCodigoDigitado,
                  child: const Text('Buscar'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _CameraArea extends StatelessWidget {
  const _CameraArea({
    required this.controller,
    required this.inicializando,
    required this.erro,
    required this.status,
    required this.automatico,
    required this.lendo,
  });

  final CameraController? controller;
  final bool inicializando;
  final String? erro;
  final String status;
  final bool automatico;
  final bool lendo;

  @override
  Widget build(BuildContext context) {
    final camera = controller;

    if (erro != null) {
      return ColoredBox(
        color: Colors.black,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Center(
            child: Text(
              'Não foi possível abrir a câmera.\n$erro',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white),
            ),
          ),
        ),
      );
    }

    if (inicializando || camera == null || !camera.value.isInitialized) {
      return const ColoredBox(
        color: Colors.black,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    return ColoredBox(
      color: Colors.black,
      child: Stack(
        fit: StackFit.expand,
        children: [
          Center(
            child: AspectRatio(
              aspectRatio: 1 / camera.value.aspectRatio,
              child: CameraPreview(camera),
            ),
          ),
          const _ScannerFrame(),
          Positioned(
            left: 16,
            right: 16,
            bottom: 16,
            child: _ScannerStatusBar(
              status: status,
              automatico: automatico,
              lendo: lendo,
            ),
          ),
        ],
      ),
    );
  }
}

class _ScannerFrame extends StatelessWidget {
  const _ScannerFrame();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        width: 280,
        height: 170,
        decoration: BoxDecoration(
          border: Border.all(color: const Color(0xfff3b35f), width: 3),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Stack(
          children: [
            Center(
              child: Container(
                height: 2,
                margin: const EdgeInsets.symmetric(horizontal: 20),
                color: const Color(0xfff3b35f),
              ),
            ),
            Positioned(
              left: 10,
              right: 10,
              bottom: 12,
              child: Text(
                'Alinhe o código dentro da moldura',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  shadows: [
                    Shadow(
                      color: Colors.black.withValues(alpha: .75),
                      blurRadius: 8,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ScannerStatusBar extends StatelessWidget {
  const _ScannerStatusBar({
    required this.status,
    required this.automatico,
    required this.lendo,
  });

  final String status;
  final bool automatico;
  final bool lendo;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: const Color(0xff241611).withValues(alpha: .88),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xfff3b35f)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Icon(
              lendo
                  ? Icons.center_focus_strong
                  : (automatico ? Icons.sensors : Icons.radio_button_checked),
              color: const Color(0xfff3b35f),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                status,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

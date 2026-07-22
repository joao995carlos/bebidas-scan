import 'dart:async';
import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../services/app_preferences.dart';

class BottleOcrPage extends StatefulWidget {
  const BottleOcrPage({super.key});

  @override
  State<BottleOcrPage> createState() => _BottleOcrPageState();
}

class _BottleOcrPageState extends State<BottleOcrPage>
    with WidgetsBindingObserver {
  static const leitorNativo = MethodChannel('bebidas_scan/native_barcode');

  final preferences = AppPreferences();
  CameraController? cameraController;
  bool cameraInicializando = true;
  bool lendo = false;
  bool emitindoSom = false;
  bool lanternaLigada = false;
  bool encerrando = false;
  bool guiaSonoroCamera = false;
  String? cameraErro;
  String status = 'Aponte para o rótulo e toque em ler rótulo.';
  String? codigoBarras;
  Map<String, dynamic>? ultimaSugestao;
  String? ultimoTexto;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    carregarPreferenciasEInicializar();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final args = ModalRoute.of(context)?.settings.arguments;
    if (args is Map && codigoBarras == null) {
      codigoBarras = args['codigo_barras']?.toString();
    }
  }

  @override
  void dispose() {
    encerrando = true;
    emitindoSom = false;
    WidgetsBinding.instance.removeObserver(this);
    encerrarCamera();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.inactive ||
        state == AppLifecycleState.paused) {
      encerrarCamera();
      return;
    }

    if (state == AppLifecycleState.resumed && !encerrando) {
      carregarPreferenciasEInicializar();
    }
  }

  Future<void> carregarPreferenciasEInicializar() async {
    final guiaSonoro = await preferences.guiaSonoroCameraAtivo();
    if (!mounted || encerrando) return;
    setState(() => guiaSonoroCamera = guiaSonoro);
    await inicializarCamera();
  }

  Future<void> inicializarCamera() async {
    setState(() {
      cameraInicializando = true;
      cameraErro = null;
      status = 'Aponte para o rótulo e toque em ler rótulo.';
    });

    try {
      final cameras = await availableCameras();
      final camera = selecionarCameraTraseira(cameras);
      if (camera == null) {
        throw CameraException(
          'no_camera',
          'Nenhuma câmera traseira encontrada.',
        );
      }

      final controller = CameraController(
        camera,
        ResolutionPreset.high,
        enableAudio: false,
      );

      await controller.initialize();
      await controller.lockCaptureOrientation(DeviceOrientation.portraitUp);
      await controller.setFocusMode(FocusMode.auto);
      await controller.setFlashMode(FlashMode.off);

      if (!mounted || encerrando) {
        await controller.dispose();
        return;
      }

      setState(() {
        cameraController = controller;
        cameraInicializando = false;
        lanternaLigada = false;
      });
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

  Future<void> lerRotulo() async {
    final controller = cameraController;
    if (controller == null || !controller.value.isInitialized || lendo) return;

    setState(() {
      lendo = true;
      ultimaSugestao = null;
      ultimoTexto = null;
      status = 'Lendo rótulo...';
    });
    iniciarSomLeitura();

    XFile? foto;
    try {
      foto = await controller.takePicture();
      if (!mounted) return;
      setState(() => status = 'Extraindo texto da imagem...');

      final resultado = await leitorNativo.invokeMapMethod<String, dynamic>(
        'scanTextImageFile',
        {'path': foto.path},
      );

      final texto = resultado?['text']?.toString() ?? '';
      final linhas = (resultado?['lines'] as List?)
              ?.map((linha) => linha.toString())
              .where((linha) => linha.trim().isNotEmpty)
              .toList() ??
          separarLinhas(texto);

      final sugestao = extrairSugestao(texto: texto, linhas: linhas);

      if (!mounted) return;
      setState(() {
        lendo = false;
        status = sugestao.isEmpty
            ? 'Texto lido, mas poucos dados foram identificados.'
            : 'Dados sugeridos. Revise antes de salvar.';
        ultimaSugestao = sugestao;
        ultimoTexto = texto;
      });
      await somConclusao();
    } catch (erro) {
      if (!mounted) return;
      setState(() {
        lendo = false;
        status =
            'Não foi possível ler o rótulo. Tente aproximar e melhorar a luz.';
      });
    } finally {
      emitindoSom = false;
      if (foto != null) {
        try {
          await File(foto.path).delete();
        } catch (_) {
          // Arquivo temporario pode ja ter sido limpo pelo sistema.
        }
      }
    }
  }

  void iniciarSomLeitura() {
    if (!guiaSonoroCamera) return;

    emitindoSom = true;
    unawaited(() async {
      while (emitindoSom && mounted) {
        await SystemSound.play(SystemSoundType.click);
        await Future<void>.delayed(const Duration(milliseconds: 650));
      }
    }());
  }

  Future<void> somConclusao() async {
    if (guiaSonoroCamera) {
      await SystemSound.play(SystemSoundType.alert);
    }
    await HapticFeedback.mediumImpact();
  }

  List<String> separarLinhas(String texto) {
    return texto
        .split(RegExp(r'[\r\n]+'))
        .map((linha) => linha.trim())
        .where((linha) => linha.isNotEmpty)
        .toList();
  }

  Map<String, dynamic> extrairSugestao({
    required String texto,
    required List<String> linhas,
  }) {
    final textoNormalizado = normalizar(texto);
    final sugestao = <String, dynamic>{};
    final cachaca = <String, dynamic>{};

    final codigo = codigoBarras;
    if (codigo != null && codigo.isNotEmpty) {
      sugestao['codigo_barras'] = codigo;
    }

    final tipo = detectarTipo(textoNormalizado);
    sugestao['tipo'] = tipo;

    final teor = RegExp(r'(\d{1,2}(?:[,.]\d{1,2})?)\s*%?\s*(?:vol|alc|alcool)?')
        .allMatches(textoNormalizado)
        .map((m) => m.group(1))
        .whereType<String>()
        .map((valor) => double.tryParse(valor.replaceAll(',', '.')))
        .whereType<double>()
        .firstWhere(
          (valor) => valor >= 5 && valor <= 80,
          orElse: () => 0,
        );
    if (teor > 0) sugestao['teor_alcoolico'] = teor;

    final volumeMl = extrairVolumeMl(textoNormalizado);
    if (volumeMl != null) cachaca['volume_ml'] = volumeMl;

    final envelhecimento = extrairEnvelhecimento(textoNormalizado);
    if (envelhecimento != null) {
      cachaca['tempo_envelhecimento_meses'] = envelhecimento;
    }

    final lote = extrairAposRotulo(
        texto,
        RegExp(r'\b(?:lote|lot|lt)\b[:\s-]*([A-Z0-9./-]+)',
            caseSensitive: false));
    if (lote != null) cachaca['lote'] = lote;

    final produtor = extrairAposRotulo(
      texto,
      RegExp(r'\b(?:produtor|produzido por|fabricado por)\b[:\s-]*([^\n\r]+)',
          caseSensitive: false),
    );
    if (produtor != null) {
      cachaca['produtor'] = limparCampoTexto(produtor);
      sugestao['marca'] ??= limparCampoTexto(produtor);
    }

    final alambique = extrairAposRotulo(
      texto,
      RegExp(r'\b(?:alambique)\b[:\s-]*([^\n\r]+)', caseSensitive: false),
    );
    if (alambique != null) cachaca['alambique'] = limparCampoTexto(alambique);

    if (textoNormalizado.contains('amburana')) {
      cachaca['madeira'] = 'Amburana';
    } else if (textoNormalizado.contains('carvalho')) {
      cachaca['madeira'] = 'Carvalho';
    } else if (textoNormalizado.contains('balsamo')) {
      cachaca['madeira'] = 'Balsamo';
    } else if (textoNormalizado.contains('jequitiba')) {
      cachaca['madeira'] = 'Jequitiba';
    }

    if (textoNormalizado.contains('extra premium')) {
      cachaca['classificacao'] = 'Extra premium';
    } else if (textoNormalizado.contains('premium')) {
      cachaca['classificacao'] = 'Premium';
    } else if (textoNormalizado.contains('prata')) {
      cachaca['classificacao'] = 'Prata';
    } else if (textoNormalizado.contains('ouro')) {
      cachaca['classificacao'] = 'Ouro';
    } else if (textoNormalizado.contains('envelhecida')) {
      cachaca['classificacao'] = 'Envelhecida';
    }

    final estado = RegExp(
            r'\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b')
        .firstMatch(texto.toUpperCase())
        ?.group(1);
    if (estado != null) cachaca['estado_origem'] = estado;

    final nome = escolherNome(linhas);
    if (nome != null) sugestao['nome'] = nome;

    final marca = escolherMarca(linhas, nome);
    if (marca != null) sugestao['marca'] ??= marca;

    if (cachaca.isNotEmpty) sugestao['cachaca'] = cachaca;
    return sugestao;
  }

  String detectarTipo(String texto) {
    if (texto.contains('cachaca') || texto.contains('aguardente')) {
      return 'cachaca';
    }
    if (texto.contains('vodka')) return 'vodka';
    if (texto.contains('gin')) return 'gin';
    if (texto.contains('whisky') || texto.contains('whiskey')) return 'whisky';
    if (texto.contains('rum')) return 'rum';
    if (texto.contains('tequila')) return 'tequila';
    return 'destilado';
  }

  int? extrairVolumeMl(String texto) {
    final litros = RegExp(r'\b(\d(?:[,.]\d{1,3})?)\s*l\b').firstMatch(texto);
    if (litros != null) {
      final valor = double.tryParse(litros.group(1)!.replaceAll(',', '.'));
      if (valor != null && valor > 0 && valor <= 5) {
        return (valor * 1000).round();
      }
    }

    final ml = RegExp(r'\b(\d{2,5})\s*m\s*l\b').firstMatch(texto);
    if (ml != null) {
      final valor = int.tryParse(ml.group(1)!);
      if (valor != null && valor >= 50 && valor <= 5000) return valor;
    }
    return null;
  }

  int? extrairEnvelhecimento(String texto) {
    final anos = RegExp(r'\b(\d{1,2})\s*anos?\b').firstMatch(texto);
    if (anos != null) {
      final valor = int.tryParse(anos.group(1)!);
      if (valor != null && valor <= 100) return valor * 12;
    }

    final meses = RegExp(r'\b(\d{1,3})\s*meses?\b').firstMatch(texto);
    if (meses != null) {
      final valor = int.tryParse(meses.group(1)!);
      if (valor != null && valor <= 1200) return valor;
    }
    return null;
  }

  String? extrairAposRotulo(String texto, RegExp regex) {
    final match = regex.firstMatch(texto);
    return match?.group(1)?.trim();
  }

  String? escolherNome(List<String> linhas) {
    final candidatas = linhas
        .map(limparCampoTexto)
        .where((linha) => linha.length >= 3 && linha.length <= 60)
        .where((linha) => !pareceDadoTecnico(linha))
        .toList();
    if (candidatas.isEmpty) return null;

    candidatas.sort((a, b) {
      final scoreB = scoreNome(b);
      final scoreA = scoreNome(a);
      return scoreB.compareTo(scoreA);
    });
    return candidatas.first;
  }

  String? escolherMarca(List<String> linhas, String? nome) {
    final candidatas = linhas
        .map(limparCampoTexto)
        .where((linha) => linha.length >= 3 && linha.length <= 40)
        .where((linha) => linha != nome)
        .where((linha) => !pareceDadoTecnico(linha))
        .toList();
    return candidatas.length > 1 ? candidatas[1] : null;
  }

  int scoreNome(String linha) {
    final n = normalizar(linha);
    var score = linha.length;
    if (n.contains('cachaca') || n.contains('aguardente')) score += 40;
    if (RegExp(r'\d').hasMatch(linha)) score -= 20;
    if (linha == linha.toUpperCase()) score += 10;
    return score;
  }

  bool pareceDadoTecnico(String linha) {
    final n = normalizar(linha);
    return n.contains('ingrediente') ||
        n.contains('validade') ||
        n.contains('lote') ||
        n.contains('fabricado') ||
        n.contains('produzido') ||
        n.contains('cnpj') ||
        n.contains('codigo') ||
        n.contains('sac') ||
        n.contains('proibida') ||
        n.contains('ministerio') ||
        n.contains('alcool') ||
        RegExp(r'^\d+[\s\w%.]*$').hasMatch(n);
  }

  String limparCampoTexto(String texto) {
    return texto
        .replaceAll(RegExp(r'\s+'), ' ')
        .replaceAll(RegExp(r'^[^A-Za-zÀ-ÿ0-9]+'), '')
        .replaceAll(RegExp(r'[^A-Za-zÀ-ÿ0-9%./ -]+$'), '')
        .trim();
  }

  String normalizar(String texto) {
    return texto
        .toLowerCase()
        .replaceAll('ç', 'c')
        .replaceAll('á', 'a')
        .replaceAll('à', 'a')
        .replaceAll('ã', 'a')
        .replaceAll('â', 'a')
        .replaceAll('é', 'e')
        .replaceAll('ê', 'e')
        .replaceAll('í', 'i')
        .replaceAll('ó', 'o')
        .replaceAll('õ', 'o')
        .replaceAll('ô', 'o')
        .replaceAll('ú', 'u');
  }

  void confirmarSugestao() {
    final sugestao = ultimaSugestao ?? <String, dynamic>{};
    if (codigoBarras != null && codigoBarras!.isNotEmpty) {
      sugestao['codigo_barras'] = codigoBarras;
    }

    Navigator.pushReplacementNamed(
      context,
      '/bebida-form',
      arguments: {'sugestao': sugestao},
    );
  }

  void cadastrarManual() {
    Navigator.pushReplacementNamed(
      context,
      '/bebida-form',
      arguments: {'codigo_barras': codigoBarras},
    );
  }

  @override
  Widget build(BuildContext context) {
    final sugestao = ultimaSugestao;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ler rótulo da garrafa'),
        actions: [
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
            child: Semantics(
              liveRegion: true,
              child: Text(status, style: const TextStyle(fontSize: 18)),
            ),
          ),
          Expanded(
            child: Semantics(
              label: 'Área da câmera para ler textos do rótulo da garrafa',
              child: _CameraArea(
                controller: cameraController,
                inicializando: cameraInicializando,
                erro: cameraErro,
              ),
            ),
          ),
          if (sugestao != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: _SugestaoCard(sugestao: sugestao),
            ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.center,
              children: [
                FilledButton.icon(
                  onPressed: lendo ? null : lerRotulo,
                  icon: const Icon(Icons.document_scanner),
                  label: Text(lendo ? 'Lendo...' : 'Ler rótulo'),
                ),
                if (sugestao != null)
                  FilledButton.icon(
                    onPressed: confirmarSugestao,
                    icon: const Icon(Icons.check),
                    label: const Text('Revisar dados'),
                  ),
                OutlinedButton(
                  onPressed: lendo ? null : cadastrarManual,
                  child: const Text('Cadastrar manualmente'),
                ),
                TextButton(
                  onPressed: lendo ? null : () => Navigator.pop(context),
                  child: const Text('Cancelar'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SugestaoCard extends StatelessWidget {
  const _SugestaoCard({required this.sugestao});

  final Map<String, dynamic> sugestao;

  @override
  Widget build(BuildContext context) {
    final cachaca = sugestao['cachaca'] is Map
        ? Map<String, dynamic>.from(sugestao['cachaca'] as Map)
        : <String, dynamic>{};
    final linhas = <String>[
      if (sugestao['nome'] != null) 'Nome: ${sugestao['nome']}',
      if (sugestao['marca'] != null) 'Marca/produtor: ${sugestao['marca']}',
      if (sugestao['tipo'] != null) 'Tipo: ${sugestao['tipo']}',
      if (sugestao['teor_alcoolico'] != null)
        'Teor: ${sugestao['teor_alcoolico']}%',
      if (cachaca['volume_ml'] != null) 'Volume: ${cachaca['volume_ml']} ml',
      if (cachaca['classificacao'] != null)
        'Classificação: ${cachaca['classificacao']}',
      if (cachaca['madeira'] != null) 'Madeira: ${cachaca['madeira']}',
      if (cachaca['produtor'] != null) 'Produtor: ${cachaca['produtor']}',
      if (cachaca['lote'] != null) 'Lote: ${cachaca['lote']}',
    ];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Sugestao encontrada',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            if (linhas.isEmpty)
              const Text('Nenhum campo confiável foi identificado.')
            else
              ...linhas.take(6).map(Text.new),
          ],
        ),
      ),
    );
  }
}

class _CameraArea extends StatelessWidget {
  const _CameraArea({
    required this.controller,
    required this.inicializando,
    required this.erro,
  });

  final CameraController? controller;
  final bool inicializando;
  final String? erro;

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
      child: Center(
        child: AspectRatio(
          aspectRatio: 1 / camera.value.aspectRatio,
          child: CameraPreview(camera),
        ),
      ),
    );
  }
}

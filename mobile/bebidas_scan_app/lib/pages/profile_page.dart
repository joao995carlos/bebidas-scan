import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/app_preferences.dart';
import '../services/permission_service.dart';
import '../services/token_service.dart';

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Perfil')),
      body: const SafeArea(child: ProfileContent()),
    );
  }
}

class ProfileContent extends StatefulWidget {
  const ProfileContent({super.key});

  @override
  State<ProfileContent> createState() => _ProfileContentState();
}

class _ProfileContentState extends State<ProfileContent> {
  final api = ApiService();
  final tokenService = TokenService();
  final permissionService = PermissionService();
  final preferences = AppPreferences();

  bool carregando = true;
  bool convidado = true;
  bool vibracaoScanner = true;
  bool lanternaAutomatica = false;
  bool guiaSonoroCamera = false;
  String modoScanner = 'obturador';
  Map<String, dynamic>? usuario;
  AppPermissionStatus? permissoes;

  @override
  void initState() {
    super.initState();
    carregar();
  }

  Future<void> carregar() async {
    final token = await tokenService.lerAccessToken();
    final statusPermissoes = await permissionService.currentStatus();
    final vibracao = await preferences.vibracaoScannerAtiva();
    final lanterna = await preferences.lanternaAutomaticaAtiva();
    final guiaSonoro = await preferences.guiaSonoroCameraAtivo();
    final modo = await preferences.modoScanner();
    if (!mounted) return;

    if (token == null) {
      setState(() {
        convidado = true;
        permissoes = statusPermissoes;
        vibracaoScanner = vibracao;
        lanternaAutomatica = lanterna;
        guiaSonoroCamera = guiaSonoro;
        modoScanner = modo;
        carregando = false;
      });
      return;
    }

    try {
      final resposta = await api.perfil();
      if (!mounted) return;
      setState(() {
        convidado = false;
        usuario = Map<String, dynamic>.from(resposta.data);
        permissoes = statusPermissoes;
        vibracaoScanner = vibracao;
        lanternaAutomatica = lanterna;
        guiaSonoroCamera = guiaSonoro;
        modoScanner = modo;
        carregando = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        convidado = true;
        permissoes = statusPermissoes;
        vibracaoScanner = vibracao;
        lanternaAutomatica = lanterna;
        guiaSonoroCamera = guiaSonoro;
        modoScanner = modo;
        carregando = false;
      });
    }
  }

  Future<void> pedirPermissoes() async {
    final status = await permissionService.requestStartupPermissions();
    if (!mounted) return;
    setState(() => permissoes = status);
    if (status.cameraPermanentlyDenied) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Ative a câmera nas configurações do Android.'),
          action: SnackBarAction(
            label: 'Abrir',
            onPressed: permissionService.openSettings,
          ),
        ),
      );
    }
  }

  Future<void> alterarVibracao(bool valor) async {
    await preferences.salvarVibracaoScanner(valor);
    if (!mounted) return;
    setState(() => vibracaoScanner = valor);
  }

  Future<void> alterarLanternaAutomatica(bool valor) async {
    await preferences.salvarLanternaAutomatica(valor);
    if (!mounted) return;
    setState(() => lanternaAutomatica = valor);
  }

  Future<void> alterarGuiaSonoroCamera(bool valor) async {
    await preferences.salvarGuiaSonoroCamera(valor);
    if (!mounted) return;
    setState(() => guiaSonoroCamera = valor);
  }

  Future<void> alterarModoScanner(String modo) async {
    await preferences.salvarModoScanner(modo);
    if (!mounted) return;
    setState(() => modoScanner = modo);
  }

  Future<void> sair() async {
    try {
      await api.logout();
    } catch (_) {
      // Mesmo que a API falhe, o app deve limpar os tokens locais.
    }
    await tokenService.limparTokens();
    if (!mounted) return;
    Navigator.pushNamedAndRemoveUntil(context, '/login', (_) => false);
  }

  @override
  Widget build(BuildContext context) {
    if (carregando) {
      return const Center(child: CircularProgressIndicator());
    }

    final dados = usuario;
    final cameraOk = permissoes?.cameraGranted == true;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'Perfil',
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        if (convidado)
          _SectionCard(
            icon: Icons.person_outline,
            title: 'Conta',
            children: [
              const Text('Você está usando sem conta.'),
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: () =>
                    Navigator.pushReplacementNamed(context, '/login'),
                icon: const Icon(Icons.login),
                label: const Text('Entrar'),
              ),
              TextButton(
                onPressed: () => Navigator.pushNamed(context, '/registrar'),
                child: const Text('Criar conta'),
              ),
            ],
          )
        else
          _SectionCard(
            icon: Icons.account_circle_outlined,
            title: 'Conta',
            children: [
              Text('Nome: ${dados?['nome'] ?? 'Não informado'}'),
              Text('Usuário: ${dados?['nome_usuario'] ?? 'Não informado'}'),
              Text('E-mail: ${dados?['email'] ?? 'Não informado'}'),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: () => Navigator.pushNamed(context, '/alterar-senha'),
                icon: const Icon(Icons.lock_reset),
                label: const Text('Alterar senha'),
              ),
            ],
          ),
        if (!convidado)
          _SectionCard(
            icon: Icons.privacy_tip_outlined,
            title: 'Privacidade e LGPD',
            children: [
              const Text(
                'Gerencie aceite, exportação CSV e exclusão de conta.',
              ),
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: () => Navigator.pushNamed(context, '/privacidade'),
                icon: const Icon(Icons.privacy_tip_outlined),
                label: const Text('Abrir privacidade'),
              ),
              TextButton.icon(
                onPressed: () => Navigator.pushNamed(
                  context,
                  '/documento-privacidade',
                  arguments: {'tipo': 'politica'},
                ),
                icon: const Icon(Icons.description_outlined),
                label: const Text('Política de Privacidade'),
              ),
              TextButton.icon(
                onPressed: () => Navigator.pushNamed(
                  context,
                  '/documento-privacidade',
                  arguments: {'tipo': 'termos'},
                ),
                icon: const Icon(Icons.article_outlined),
                label: const Text('Termos de Uso'),
              ),
            ],
          ),
        _SectionCard(
          icon: Icons.settings_outlined,
          title: 'Configurações',
          children: [
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: Icon(
                cameraOk ? Icons.check_circle : Icons.error_outline,
                color: cameraOk
                    ? Theme.of(context).colorScheme.primary
                    : Theme.of(context).colorScheme.error,
              ),
              title: const Text('Permissão de câmera'),
              subtitle: Text(
                cameraOk
                    ? 'Liberada para scanner e OCR.'
                    : 'Necessária para escanear códigos e rótulos.',
              ),
              trailing: TextButton(
                onPressed: pedirPermissoes,
                child: Text(cameraOk ? 'Revisar' : 'Permitir'),
              ),
            ),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              secondary: const Icon(Icons.vibration),
              title: const Text('Vibração ao escanear'),
              subtitle:
                  const Text('Feedback curto quando um código é detectado.'),
              value: vibracaoScanner,
              onChanged: alterarVibracao,
            ),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              secondary: const Icon(Icons.hearing),
              title: const Text('Guia sonoro de câmera'),
              subtitle: const Text(
                'Sons ajudam a acompanhar a leitura de códigos e rótulos.',
              ),
              value: guiaSonoroCamera,
              onChanged: alterarGuiaSonoroCamera,
            ),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              secondary: const Icon(Icons.flashlight_on),
              title: const Text('Flash automático'),
              subtitle: const Text('Liga a lanterna ao abrir o scanner.'),
              value: lanternaAutomatica,
              onChanged: alterarLanternaAutomatica,
            ),
            const SizedBox(height: 8),
            const Text(
              'Leitura do código',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(
                  value: 'obturador',
                  icon: Icon(Icons.radio_button_checked),
                  label: Text('Obturador'),
                ),
                ButtonSegment(
                  value: 'automatico',
                  icon: Icon(Icons.center_focus_strong),
                  label: Text('Automático'),
                ),
              ],
              selected: {modoScanner},
              onSelectionChanged: (valores) =>
                  alterarModoScanner(valores.first),
            ),
            const SizedBox(height: 12),
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.slideshow_outlined),
              title: const Text('Guia do app'),
              subtitle: const Text('Rever os slides de introdução.'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => Navigator.pushNamed(context, '/onboarding'),
            ),
          ],
        ),
        if (!convidado)
          OutlinedButton.icon(
            onPressed: sair,
            icon: const Icon(Icons.logout),
            label: const Text('Sair da conta'),
          ),
      ],
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({
    required this.icon,
    required this.title,
    required this.children,
  });

  final IconData icon;
  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...children,
          ],
        ),
      ),
    );
  }
}

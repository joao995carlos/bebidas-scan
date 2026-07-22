# Bebidas Scan App

Codigo Flutter do app Android.

Como o Flutter nao esta instalado neste computador, o esqueleto Android completo nao foi gerado automaticamente. Quando o SDK estiver disponivel, rode:

```powershell
flutter create --platforms=android .
flutter pub get
flutter run
```

Se o backend estiver rodando no mesmo computador e o app estiver em um emulador Android, mantenha `apiBaseUrl` como `http://10.0.2.2:8000`.

Para celular fisico, use o IP local do computador, por exemplo:

```dart
const apiBaseUrl = 'http://192.168.0.10:8000';
```


import 'package:permission_handler/permission_handler.dart';

class AppPermissionStatus {
  const AppPermissionStatus({
    required this.cameraGranted,
    required this.cameraPermanentlyDenied,
  });

  final bool cameraGranted;
  final bool cameraPermanentlyDenied;
}

class PermissionService {
  Future<AppPermissionStatus> requestStartupPermissions() async {
    final camera = await Permission.camera.request();
    return AppPermissionStatus(
      cameraGranted: camera.isGranted,
      cameraPermanentlyDenied: camera.isPermanentlyDenied,
    );
  }

  Future<AppPermissionStatus> currentStatus() async {
    final camera = await Permission.camera.status;
    return AppPermissionStatus(
      cameraGranted: camera.isGranted,
      cameraPermanentlyDenied: camera.isPermanentlyDenied,
    );
  }

  Future<void> openSettings() {
    return openAppSettings();
  }
}

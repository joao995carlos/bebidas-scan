import 'package:bebidas_scan_app/main.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Bebidas Scan app can be created', () {
    const app = BebidasScanApp();

    expect(app, isA<BebidasScanApp>());
  });
}

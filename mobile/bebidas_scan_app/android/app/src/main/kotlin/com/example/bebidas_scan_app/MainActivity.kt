package com.example.bebidas_scan_app

import android.graphics.BitmapFactory
import android.net.Uri
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.embedding.android.FlutterActivity
import io.flutter.plugin.common.MethodChannel
import java.io.File

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            "bebidas_scan/native_barcode"
        ).setMethodCallHandler { call, result ->
            when (call.method) {
                "scanImageFile" -> {
                    val path = call.argument<String>("path")
                    if (path.isNullOrBlank()) {
                        result.error("invalid_path", "Caminho da imagem vazio.", null)
                        return@setMethodCallHandler
                    }

                    scanImageFile(path, result)
                }
                "scanImageInfoFile" -> {
                    val path = call.argument<String>("path")
                    if (path.isNullOrBlank()) {
                        result.error("invalid_path", "Caminho da imagem vazio.", null)
                        return@setMethodCallHandler
                    }

                    scanImageInfoFile(path, result)
                }
                "scanTextImageFile" -> {
                    val path = call.argument<String>("path")
                    if (path.isNullOrBlank()) {
                        result.error("invalid_path", "Caminho da imagem vazio.", null)
                        return@setMethodCallHandler
                    }

                    scanTextImageFile(path, result)
                }
                else -> result.notImplemented()
            }
        }
    }

    private fun scanImageFile(path: String, result: MethodChannel.Result) {
        val scanner = BarcodeScanning.getClient(
            BarcodeScannerOptions.Builder()
                .setBarcodeFormats(
                    Barcode.FORMAT_EAN_13,
                    Barcode.FORMAT_EAN_8,
                    Barcode.FORMAT_UPC_A,
                    Barcode.FORMAT_UPC_E,
                    Barcode.FORMAT_CODE_128
                )
                .build()
        )

        try {
            val image = InputImage.fromFilePath(this, Uri.fromFile(File(path)))
            scanner.process(image)
                .addOnSuccessListener { barcodes ->
                    val code = barcodes
                        .mapNotNull { it.rawValue?.trim() }
                        .firstOrNull { it.isNotEmpty() }

                    scanner.close()
                    result.success(code)
                }
                .addOnFailureListener { error ->
                    scanner.close()
                    result.error(
                        "scan_error",
                        error.localizedMessage ?: error.javaClass.simpleName,
                        null
                    )
                }
        } catch (error: Exception) {
            scanner.close()
            result.error(
                "scan_error",
                error.localizedMessage ?: error.javaClass.simpleName,
                null
            )
        }
    }

    private fun scanImageInfoFile(path: String, result: MethodChannel.Result) {
        val scanner = BarcodeScanning.getClient(
            BarcodeScannerOptions.Builder()
                .setBarcodeFormats(
                    Barcode.FORMAT_EAN_13,
                    Barcode.FORMAT_EAN_8,
                    Barcode.FORMAT_UPC_A,
                    Barcode.FORMAT_UPC_E,
                    Barcode.FORMAT_CODE_128
                )
                .build()
        )

        try {
            val boundsOptions = BitmapFactory.Options().apply {
                inJustDecodeBounds = true
            }
            BitmapFactory.decodeFile(path, boundsOptions)

            val image = InputImage.fromFilePath(this, Uri.fromFile(File(path)))
            scanner.process(image)
                .addOnSuccessListener { barcodes ->
                    val barcode = barcodes
                        .firstOrNull { barcode ->
                            val value = barcode.rawValue?.trim()
                            !value.isNullOrEmpty()
                        }
                    val box = barcode?.boundingBox

                    scanner.close()
                    if (barcode == null) {
                        result.success(null)
                        return@addOnSuccessListener
                    }

                    result.success(
                        mapOf(
                            "code" to barcode.rawValue?.trim(),
                            "imageWidth" to boundsOptions.outWidth,
                            "imageHeight" to boundsOptions.outHeight,
                            "left" to box?.left,
                            "top" to box?.top,
                            "right" to box?.right,
                            "bottom" to box?.bottom,
                            "centerX" to box?.centerX(),
                            "centerY" to box?.centerY()
                        )
                    )
                }
                .addOnFailureListener { error ->
                    scanner.close()
                    result.error(
                        "scan_error",
                        error.localizedMessage ?: error.javaClass.simpleName,
                        null
                    )
                }
        } catch (error: Exception) {
            scanner.close()
            result.error(
                "scan_error",
                error.localizedMessage ?: error.javaClass.simpleName,
                null
            )
        }
    }

    private fun scanTextImageFile(path: String, result: MethodChannel.Result) {
        val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)

        try {
            val image = InputImage.fromFilePath(this, Uri.fromFile(File(path)))
            recognizer.process(image)
                .addOnSuccessListener { visionText ->
                    val lines = visionText.textBlocks
                        .flatMap { block -> block.lines }
                        .map { line -> line.text.trim() }
                        .filter { line -> line.isNotEmpty() }

                    recognizer.close()
                    result.success(
                        mapOf(
                            "text" to visionText.text.trim(),
                            "lines" to lines
                        )
                    )
                }
                .addOnFailureListener { error ->
                    recognizer.close()
                    result.error(
                        "ocr_error",
                        error.localizedMessage ?: error.javaClass.simpleName,
                        null
                    )
                }
        } catch (error: Exception) {
            recognizer.close()
            result.error(
                "ocr_error",
                error.localizedMessage ?: error.javaClass.simpleName,
                null
            )
        }
    }
}

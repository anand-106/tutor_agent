import 'package:get/get.dart';
import 'package:agent/models/document.dart';
import 'package:agent/services/api_service.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:html' as html;

class DocumentController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();
  final RxList<Document> documents = <Document>[].obs;
  final RxBool isUploading = false.obs;

  Future<void> uploadDocument() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'docx', 'txt'],
        withData: true, // Important for web
      );

      if (result != null && result.files.isNotEmpty) {
        isUploading.value = true;

        final file = result.files.first;
        await _apiService.uploadDocument(file);

        documents.add(Document(
          name: file.name,
          path: file.name, // Just use name for web
        ));

        Get.snackbar('Success', 'Document uploaded successfully');
      }
    } catch (e) {
      Get.snackbar('Error', 'Failed to upload document: $e');
    } finally {
      isUploading.value = false;
    }
  }
}

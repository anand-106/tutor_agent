import 'package:get/get.dart';
import 'package:file_picker/file_picker.dart';
import 'package:agent/services/api_service.dart';
import 'package:flutter/material.dart';

class DocumentController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();
  final RxBool isUploading = false.obs;
  final RxList<DocumentInfo> documents = <DocumentInfo>[].obs;
  final Rx<Map<String, dynamic>> topics =
      Rx<Map<String, dynamic>>({'status': 'empty', 'topics': []});

  @override
  void onInit() {
    super.onInit();
    topics.value = {'status': 'empty', 'topics': []};
  }

  Future<void> uploadDocument() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'docx', 'txt'],
      );

      if (result != null) {
        isUploading.value = true;
        final file = result.files.first;

        final success = await _apiService.uploadDocument(
          file.bytes!,
          file.name,
        );

        if (success) {
          documents.add(DocumentInfo(
            name: file.name,
            uploadTime: DateTime.now(),
          ));

          // Reset topics and fetch new ones
          topics.value = {'status': 'loading', 'topics': []};

          // Fetch topics after successful upload
          await refreshTopics();

          Get.snackbar(
            'Success',
            'Document uploaded successfully',
            backgroundColor: Colors.green.withOpacity(0.1),
            colorText: Colors.white,
            duration: Duration(seconds: 3),
          );
        } else {
          Get.snackbar(
            'Error',
            'Failed to upload document',
            backgroundColor: Colors.red.withOpacity(0.1),
            colorText: Colors.white,
            duration: Duration(seconds: 3),
          );
        }
      }
    } catch (e) {
      Get.snackbar(
        'Error',
        'Failed to upload document: $e',
        backgroundColor: Colors.red.withOpacity(0.1),
        colorText: Colors.white,
        duration: Duration(seconds: 3),
      );
    } finally {
      isUploading.value = false;
    }
  }

  Future<Map<String, dynamic>> getTopics() async {
    try {
      if (topics.value['status'] == 'empty' ||
          topics.value['status'] == 'error') {
        await refreshTopics();
      }
      return topics.value;
    } catch (e) {
      topics.value = {
        'status': 'error',
        'message': 'Failed to load topics: $e',
        'topics': []
      };
      return topics.value;
    }
  }

  Future<void> refreshTopics() async {
    try {
      topics.value = {'status': 'loading', 'topics': []};

      final response = await _apiService.getTopics();
      print('API Response: $response'); // Debug print

      if (response.containsKey('topics')) {
        final topicsList = response['topics'];
        if (topicsList is List && topicsList.isNotEmpty) {
          // The topics are already in the correct format
          topics.value = {'status': 'success', 'topics': topicsList};
        } else if (response['topics'] is Map<String, dynamic>) {
          // Extract from the document structure
          final documentTopics = response['topics'] as Map<String, dynamic>;
          if (documentTopics.isNotEmpty) {
            final firstDocument = documentTopics.values.first;
            if (firstDocument is Map<String, dynamic>) {
              final mainTopics = firstDocument['topics'] as List? ?? [];
              topics.value = {'status': 'success', 'topics': mainTopics};
            }
          }
        }
      }

      print('Final processed topics: ${topics.value}'); // Debug print
    } catch (e) {
      print('Error refreshing topics: $e');
      topics.value = {
        'status': 'error',
        'message': 'Failed to refresh topics: $e',
        'topics': []
      };
    }
  }
}

class DocumentInfo {
  final String name;
  final DateTime uploadTime;

  DocumentInfo({
    required this.name,
    required this.uploadTime,
  });
}

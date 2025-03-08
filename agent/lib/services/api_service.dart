import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:get/get.dart';
import 'package:dio/dio.dart' as dio;

class ApiService extends GetxService {
  final dio.Dio _dio = dio.Dio();
  static const String baseUrl = 'http://127.0.0.1:8000/api';

  @override
  void onInit() {
    super.onInit();
    _dio.options.baseUrl = baseUrl;
    _dio.options.connectTimeout = Duration(seconds: 60);
    _dio.options.receiveTimeout = Duration(seconds: 60);
    _dio.options.sendTimeout = Duration(seconds: 60);
  }

  Future<String> sendChatMessage(String text) async {
    try {
      final response = await _dio.post(
        '/chat',
        data: {'text': text},
      );

      if (response.statusCode == 200 && response.data['response'] != null) {
        return response.data['response'];
      }
      throw 'Invalid response from server';
    } catch (e) {
      throw 'Failed to send message: $e';
    }
  }

  Future<bool> uploadDocument(List<int> fileBytes, String fileName) async {
    try {
      final formData = dio.FormData.fromMap({
        'file': dio.MultipartFile.fromBytes(
          fileBytes,
          filename: fileName,
        ),
      });

      final response = await _dio.post(
        '/upload',
        data: formData,
      );

      return response.statusCode == 200;
    } catch (e) {
      throw 'Error uploading document: $e';
    }
  }

  Future<Map<String, dynamic>> getTopics() async {
    try {
      // Use http package instead of Dio for this request to avoid web issues
      final response = await http.get(Uri.parse('$baseUrl/topics'));

      if (response.statusCode == 200) {
        final responseData = json.decode(response.body);
        print('Raw API Response: $responseData'); // Debug print

        if (responseData == null) {
          return {
            'status': 'error',
            'message': 'Invalid response from server',
            'topics': []
          };
        }

        // If the response is already a Map<String, dynamic>
        if (responseData is Map<String, dynamic>) {
          final topics = responseData['topics'];
          if (topics is Map<String, dynamic>) {
            // Get the first document entry
            final firstDocumentEntry = topics.entries.first;
            final documentData = firstDocumentEntry.value;

            if (documentData is Map<String, dynamic>) {
              return {
                'status': 'success',
                'topics': [
                  {
                    'title': documentData['title'] ?? '',
                    'content': documentData['content'] ?? '',
                    'subtopics': documentData['topics'] ?? []
                  }
                ]
              };
            }
          }
        }

        return {'status': 'success', 'topics': responseData['topics'] ?? []};
      }

      return {
        'status': 'error',
        'message': 'Server returned status ${response.statusCode}',
        'topics': []
      };
    } catch (e) {
      print('Error getting topics: $e');
      return {
        'status': 'error',
        'message': 'Failed to get topics: $e',
        'topics': []
      };
    }
  }
}

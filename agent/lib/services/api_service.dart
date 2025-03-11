import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:get/get.dart';
import 'package:dio/dio.dart' as dio;

class ApiService extends GetxService {
  final dio.Dio _dio = dio.Dio();
  static const String baseUrl = 'http://127.0.0.1:8000/api';

  Future<ApiService> init() async {
    _dio.options.baseUrl = baseUrl;
    _dio.options.connectTimeout = Duration(seconds: 60);
    _dio.options.receiveTimeout = Duration(seconds: 60);
    _dio.options.sendTimeout = Duration(seconds: 60);
    return this;
  }

  @override
  void onInit() {
    super.onInit();
  }

  Future<dynamic> sendChatMessage(String text) async {
    try {
      final response = await _dio.post(
        '/chat',
        data: {'text': text},
      );

      if (response.statusCode == 200) {
        if (response.data is Map<String, dynamic>) {
          final data = response.data as Map<String, dynamic>;
          print('Raw API Response: $data'); // Debug log

          // Check if this is a diagram response
          if (data['has_diagram'] == true && data['mermaid_code'] != null) {
            print('Received diagram response from API'); // Debug log

            // Clean up the Mermaid code by removing any extra backticks or mermaid tags
            String mermaidCode = data['mermaid_code'] as String;
            print('Original Mermaid code: $mermaidCode'); // Debug log

            mermaidCode = mermaidCode
                .replaceAll('```mermaid', '')
                .replaceAll('```', '')
                .trim();
            print('Cleaned Mermaid code: $mermaidCode'); // Debug log

            // Ensure proper diagram type prefix
            String diagramType = data['diagram_type'] ?? 'flowchart';
            print('Diagram type: $diagramType'); // Debug log

            if (!mermaidCode.startsWith('graph') &&
                !mermaidCode.startsWith('sequenceDiagram') &&
                !mermaidCode.startsWith('classDiagram')) {
              if (diagramType == 'sequence') {
                mermaidCode = 'sequenceDiagram\n' + mermaidCode;
              } else if (diagramType == 'class') {
                mermaidCode = 'classDiagram\n' + mermaidCode;
              } else {
                mermaidCode = 'graph TD\n' + mermaidCode;
              }
            }

            print('Final formatted Mermaid code: $mermaidCode'); // Debug log

            // Return the formatted response
            return {
              'response': data['response'],
              'has_diagram': true,
              'mermaid_code': mermaidCode,
              'diagram_type': diagramType
            };
          }
          return data;
        }
        return {'response': response.data['response'], 'has_diagram': false};
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
        return responseData;
      }
      throw 'Failed to get topics';
    } catch (e) {
      throw 'Error getting topics: $e';
    }
  }
}

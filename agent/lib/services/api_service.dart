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

  // User progress tracking methods
  Future<Map<String, dynamic>> getUserKnowledgeSummary(String userId) async {
    try {
      final response =
          await http.get(Uri.parse('$baseUrl/user/$userId/knowledge'));

      if (response.statusCode == 200) {
        final responseData = json.decode(response.body);
        print('User Knowledge Summary: $responseData'); // Debug print
        return responseData;
      }
      throw 'Failed to get user knowledge summary';
    } catch (e) {
      throw 'Error getting user knowledge summary: $e';
    }
  }

  Future<Map<String, dynamic>> getTopicProgress(
      String userId, String topic) async {
    try {
      final encodedTopic = Uri.encodeComponent(topic);
      final response = await http
          .get(Uri.parse('$baseUrl/user/$userId/topic/$encodedTopic'));

      if (response.statusCode == 200) {
        final responseData = json.decode(response.body);
        print('Topic Progress: $responseData'); // Debug print
        return responseData;
      }
      throw 'Failed to get topic progress';
    } catch (e) {
      throw 'Error getting topic progress: $e';
    }
  }

  Future<Map<String, dynamic>> getLearningPatterns(String userId) async {
    try {
      final response =
          await http.get(Uri.parse('$baseUrl/user/$userId/patterns'));

      if (response.statusCode == 200) {
        final responseData = json.decode(response.body);
        print('Learning Patterns: $responseData'); // Debug print
        return responseData;
      }

      // Return default structure on error
      print(
          'Failed to get learning patterns: Status code ${response.statusCode}');
      return {
        "user_id": userId,
        "interaction_counts": {},
        "study_regularity": "none",
        "insights": []
      };
    } catch (e) {
      print('Error getting learning patterns: $e');
      // Return default structure on exception
      return {
        "user_id": userId,
        "interaction_counts": {},
        "study_regularity": "none",
        "insights": []
      };
    }
  }

  Future<Map<String, dynamic>> trackUserInteraction(
    String userId,
    String interactionType, {
    String? topic,
    int? score,
    List<Map<String, dynamic>>? questions,
    int? durationMinutes,
    int? cardsReviewed,
    int? correctRecalls,
    int? viewDurationSeconds,
  }) async {
    try {
      final data = {
        'user_id': userId,
        'interaction_type': interactionType,
        if (topic != null) 'topic': topic,
        if (score != null) 'score': score,
        if (questions != null) 'questions': questions,
        if (durationMinutes != null) 'duration_minutes': durationMinutes,
        if (cardsReviewed != null) 'cards_reviewed': cardsReviewed,
        if (correctRecalls != null) 'correct_recalls': correctRecalls,
        if (viewDurationSeconds != null)
          'view_duration_seconds': viewDurationSeconds,
      };

      final response = await _dio.post(
        '/user/track',
        data: data,
      );

      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      throw 'Failed to track user interaction';
    } catch (e) {
      throw 'Error tracking user interaction: $e';
    }
  }
}

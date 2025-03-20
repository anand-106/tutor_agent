import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:get/get.dart';
import 'package:dio/dio.dart' as dio;
import 'dart:math' as math;

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

  Future<dynamic> sendChatMessage(String text,
      {String userId = 'default_user'}) async {
    try {
      // Check if the message is a special command (starts with !)
      // We'll still send it to the API but avoid trying to parse these as JSON
      bool isSpecialCommand = text.trim().startsWith('!');
      if (isSpecialCommand) {
        print(
            'Sending special command to API: ${text.substring(0, math.min(20, text.length))}...');
      }

      final response = await _dio.post(
        '/chat',
        data: {'text': text, 'user_id': userId},
      );

      if (response.statusCode == 200) {
        if (response.data is Map<String, dynamic>) {
          final data = response.data as Map<String, dynamic>;
          print('Raw API Response: $data'); // Debug log

          // Check if this is a question response
          if (data.containsKey('question') &&
              data.containsKey('has_question') &&
              data['has_question'] == true) {
            print('Received question response from API');
            return data; // Return the full question data structure
          }

          // Check if this is a lesson plan response
          if (data.containsKey('lesson_plan') &&
              data.containsKey('has_lesson_plan') &&
              data['has_lesson_plan'] == true) {
            print('Received lesson plan response from API');
            return data;
          }

          // Check if this is a diagram response
          if (data.containsKey('has_diagram') &&
              data['has_diagram'] == true &&
              data.containsKey('mermaid_code') &&
              data['mermaid_code'] != null) {
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

            // Return the diagram data with the response text
            return {
              'response': data['response'] ?? '',
              'has_diagram': true,
              'mermaid_code': mermaidCode,
              'diagram_type': diagramType
            };
          }

          // Check if this is a flashcard response
          if (data.containsKey('flashcards') && data.containsKey('topic')) {
            print('Received flashcard response from API'); // Debug log

            final flashcards = data['flashcards'] as List;
            final topic = data['topic'] as String? ?? 'Study Topic';

            // Extract the flashcard data and return it directly
            if (flashcards.isNotEmpty) {
              print(
                  'Flashcards contains ${flashcards.length} cards on topic: $topic'); // Debug log

              // Return the flashcard data with the response text
              return {
                'response': data['response'] ?? '',
                'flashcards': flashcards,
                'topic': topic,
                'description': data['description'] ??
                    'Study these flashcards to improve your understanding'
              };
            }
          }

          // Default case - just return the data
          return data;
        } else if (response.data is String) {
          // Handle plain text responses
          print(
              'Received plain text response from API: ${response.data.toString().substring(0, math.min(50, response.data.toString().length))}...');
          return {'response': response.data.toString(), 'has_diagram': false};
        } else {
          // Handle any other response type
          print(
              'Received non-map response from API: ${response.data.runtimeType}');
          return {'response': response.data.toString(), 'has_diagram': false};
        }
      } else if (response.statusCode == 429) {
        // Too many requests
        return {
          'response':
              'The server is currently busy. Please try again in a moment.',
          'has_diagram': false,
          'error': 'rate_limit'
        };
      }
      throw 'Invalid response from server: ${response.statusCode}';
    } catch (e) {
      print('Error in sendChatMessage: $e');
      return {
        'response': 'Error communicating with the server: $e',
        'has_diagram': false,
        'error': 'communication'
      };
    }
  }

  Future<Map<String, dynamic>> uploadDocument(
      List<int> fileBytes, String fileName) async {
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

      if (response.statusCode == 200) {
        // Check if the response contains a lesson plan
        if (response.data is Map<String, dynamic>) {
          return response.data as Map<String, dynamic>;
        }
        return {'message': 'Document uploaded successfully'};
      }
      throw 'Failed to upload document';
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

  // Add these methods for lesson plan generation
  Future<Map<String, dynamic>> generateLessonPlan(
    String userId,
    String topic,
    double knowledgeLevel, {
    List<Map<String, dynamic>>? subtopics,
    int timeAvailable = 60,
  }) async {
    try {
      final data = {
        'user_id': userId,
        'topic': topic,
        'knowledge_level': knowledgeLevel,
        if (subtopics != null) 'subtopics': subtopics,
        'time_available': timeAvailable,
      };

      final response = await _dio.post(
        '/generate-lesson-plan',
        data: data,
      );

      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      throw 'Failed to generate lesson plan';
    } catch (e) {
      throw 'Error generating lesson plan: $e';
    }
  }

  Future<Map<String, dynamic>> generateCurriculum(
    String userId,
    List<Map<String, dynamic>> topics, {
    int totalTimeAvailable = 600,
  }) async {
    try {
      final data = {
        'user_id': userId,
        'topics': topics,
        'total_time_available': totalTimeAvailable,
      };

      final response = await _dio.post(
        '/generate-curriculum',
        data: data,
      );

      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      throw 'Failed to generate curriculum';
    } catch (e) {
      throw 'Error generating curriculum: $e';
    }
  }
}

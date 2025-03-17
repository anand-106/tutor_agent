import 'package:get/get.dart';
import 'package:file_picker/file_picker.dart';
import 'package:agent/services/api_service.dart';
import 'package:flutter/material.dart';
import 'package:agent/controllers/lesson_plan_controller.dart';
import 'package:agent/controllers/user_progress_controller.dart';
import 'package:agent/models/lesson_plan.dart';

class DocumentController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();
  final LessonPlanController _lessonPlanController =
      Get.find<LessonPlanController>();
  final UserProgressController _userProgressController =
      Get.find<UserProgressController>();
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

        final response = await _apiService.uploadDocument(
          file.bytes!,
          file.name,
        );

        if (response.containsKey('message')) {
          documents.add(DocumentInfo(
            name: file.name,
            uploadTime: DateTime.now(),
          ));

          // Reset topics and fetch new ones
          topics.value = {'status': 'loading', 'topics': []};

          // Check if the response contains topics
          if (response.containsKey('topics')) {
            topics.value = {
              'status': 'success',
              'topics': response['topics']['topics']
            };
          } else {
            // Fetch topics after successful upload if not included in response
            await refreshTopics();
          }

          // Check if the response contains a lesson plan
          if (response.containsKey('lesson_plan')) {
            // Use the lesson plan from the response
            _lessonPlanController.currentLessonPlan.value =
                await _createLessonPlanFromResponse(response['lesson_plan']);

            // Navigate to the lesson plan view
            Get.toNamed('/lesson-plan');
          } else {
            // Generate lesson plans for the main topics if not included in response
            await _generateLessonPlansFromTopics();
          }

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

  Future<void> _generateLessonPlansFromTopics() async {
    try {
      // Check if we have topics
      if (topics.value['status'] != 'success' ||
          topics.value['topics'] == null ||
          (topics.value['topics'] as List).isEmpty) {
        print('No topics available for lesson plan generation');
        return;
      }

      final topicsList = topics.value['topics'] as List;

      // Get the first main topic
      if (topicsList.isNotEmpty) {
        final mainTopic = topicsList[0];

        // Extract topic name and subtopics
        final String topicName = mainTopic['title'];
        final List<dynamic> rawSubtopics = mainTopic['subtopics'] ?? [];

        // Convert subtopics to the required format
        final List<Map<String, dynamic>> subtopics =
            rawSubtopics.map((subtopic) {
          return {
            'title': subtopic['title'],
            'content': subtopic['content'],
          };
        }).toList();

        // Track the topic view to update knowledge tracking
        await _userProgressController.trackTopicView(
            topicName, 60); // 60 seconds view time

        // Generate a lesson plan for this topic
        await _lessonPlanController.generateLessonPlan(
          topicName,
          subtopics: subtopics,
          timeAvailable: 60, // Default to 60 minutes
        );

        print('Generated lesson plan for topic: $topicName');

        // Navigate to the lesson plan view
        Get.toNamed('/lesson-plan');
      }
    } catch (e) {
      print('Error generating lesson plans from topics: $e');
    }
  }

  // Helper method to create a LessonPlan from the API response
  Future<LessonPlan> _createLessonPlanFromResponse(
      Map<String, dynamic> lessonPlanData) async {
    try {
      // Create a LessonPlan from the response data
      return LessonPlan.fromJson(lessonPlanData);
    } catch (e) {
      print('Error creating lesson plan from response: $e');
      throw e;
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

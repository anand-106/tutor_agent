import 'package:get/get.dart';
import 'package:file_picker/file_picker.dart';
import 'package:agent/services/api_service.dart';
import 'package:flutter/material.dart';
import 'package:agent/controllers/lesson_plan_controller.dart';
import 'package:agent/controllers/user_progress_controller.dart';
import 'package:agent/models/lesson_plan.dart';
import 'package:agent/controllers/chat_controller.dart';

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

  // Get the chat controller
  late final ChatController _chatController;

  @override
  void onInit() {
    super.onInit();
    topics.value = {'status': 'empty', 'topics': []};

    // Initialize the chat controller
    _chatController = Get.find<ChatController>();
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

          // Reset topics and fetch new ones in the background
          topics.value = {'status': 'loading', 'topics': []};

          // Check if the response contains topics
          if (response.containsKey('topics')) {
            try {
              print('Upload response contains topics: ${response['topics']}');
              final uploadTopics = response['topics'];

              if (uploadTopics is List) {
                // Direct list of topics - simplest and expected case
                topics.value = {'status': 'success', 'topics': uploadTopics};
                print(
                    'Upload provided a clean list of ${uploadTopics.length} topics');
              } else if (uploadTopics is Map<String, dynamic>) {
                // Handle the case where it's a map with a topics field
                if (uploadTopics.containsKey('topics') &&
                    uploadTopics['topics'] is List) {
                  topics.value = {
                    'status': 'success',
                    'topics': uploadTopics['topics']
                  };
                  print(
                      'Extracted topics list from nested map in upload response');
                } else {
                  // Treat it as a single topic if it has a title
                  if (uploadTopics.containsKey('title')) {
                    topics.value = {
                      'status': 'success',
                      'topics': [uploadTopics]
                    };
                    print('Treating topics map as a single topic');
                  } else {
                    // Fallback - fetch topics separately
                    print('Topics structure unrecognized, fetching separately');
                    await refreshTopics();
                  }
                }
              } else {
                // Not a list or map - fetch topics separately
                print(
                    'Unexpected topics type in upload response: ${uploadTopics.runtimeType}');
                await refreshTopics();
              }
            } catch (e) {
              print('Error processing topics from upload response: $e');
              await refreshTopics();
            }
          } else {
            // Fetch topics after successful upload if not included in response
            await refreshTopics();
          }

          // Clear any existing chat
          _chatController.clearChat();

          // Navigate to the topics tab after successful upload
          Get.toNamed('/topics');

          Get.snackbar(
            'Success',
            'Document uploaded successfully. Press "Start Studying" to begin learning.',
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
      print('API Response for topics: $response'); // Debug print

      if (response.containsKey('topics')) {
        final topicsList = response['topics'];

        if (topicsList is List) {
          // Direct list of topics - simplest case
          topics.value = {'status': 'success', 'topics': topicsList};
          print(
              'Topics loaded successfully as list: ${topicsList.length} topics');
        } else if (topicsList is Map<String, dynamic>) {
          // It's a map structure - need to extract the actual topics list
          print('Topics returned as map, extracting list from structure');

          // Check if it has a topics field (nested structure)
          if (topicsList.containsKey('topics') &&
              topicsList['topics'] is List) {
            topics.value = {
              'status': 'success',
              'topics': topicsList['topics']
            };
            print('Extracted topics list from nested map');
          } else if (topicsList.isNotEmpty) {
            // Try to extract from the document structure (older API)
            try {
              final firstDocument = topicsList.values.first;
              if (firstDocument is Map<String, dynamic> &&
                  firstDocument.containsKey('topics') &&
                  firstDocument['topics'] is List) {
                topics.value = {
                  'status': 'success',
                  'topics': firstDocument['topics']
                };
                print('Extracted topics from document structure');
              } else {
                // Fallback - wrap the map in a list
                topics.value = {
                  'status': 'success',
                  'topics': [topicsList]
                };
                print('Using map as a single topic');
              }
            } catch (e) {
              print('Error extracting from map structure: $e');
              topics.value = {
                'status': 'success',
                'topics': [topicsList]
              };
            }
          } else {
            // Empty map
            topics.value = {'status': 'success', 'topics': []};
            print('Topics map is empty');
          }
        } else {
          // Not a list or map - convert to string and use as title
          print(
              'Topics returned as unexpected type: ${topicsList.runtimeType}');
          topics.value = {
            'status': 'success',
            'topics': [
              {
                'title': topicsList.toString(),
                'content': 'Topic content converted from non-standard format',
                'subtopics': []
              }
            ]
          };
        }
      } else {
        // No topics key
        topics.value = {'status': 'success', 'topics': []};
        print('No topics key in API response');
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

  Future<void> studyTopic(String topicTitle) async {
    try {
      // Get the chat controller
      final chatController = Get.find<ChatController>();

      // Clean up the topic title (remove extra quotes or special characters)
      final cleanTopicTitle = topicTitle.trim();

      // Check if the topic exists in our topics list
      bool topicExists = false;
      if (topics.value['status'] == 'success' &&
          topics.value['topics'] is List) {
        final topicsList = topics.value['topics'] as List;
        for (var topic in topicsList) {
          if (topic is Map && topic['title'] == cleanTopicTitle) {
            topicExists = true;
            break;
          }
        }
      }

      // Log the attempt
      print(
          'Starting study on topic: $cleanTopicTitle (exists in topic list: $topicExists)');

      // Clear any existing chat
      chatController.clearChat();

      // Navigate to the chat tab
      Get.toNamed('/chat');

      // Add a system message about starting to study the topic
      chatController.addSystemMessage(
          'Starting a discussion about "$cleanTopicTitle". You can ask questions and explore this topic freely.');

      // Send a special command to initiate a direct topic discussion without creating a lesson plan
      chatController.sendMessage("!study_topic:$cleanTopicTitle");
    } catch (e) {
      print('Error starting topic study: $e');
      Get.snackbar(
        'Error',
        'Failed to start topic study: $e',
        backgroundColor: Colors.red.withOpacity(0.1),
        colorText: Colors.white,
        duration: Duration(seconds: 3),
      );
    }
  }

  // Start the dynamic flow for studying
  Future<void> startStudyingFlow() async {
    try {
      // Get the chat controller
      final ChatController chatController = Get.find<ChatController>();

      // Clear any existing chat first
      chatController.clearChat();

      // Navigate to chat tab if we're not already there
      Get.toNamed('/chat');

      // Add a system message about starting the learning flow
      chatController.addSystemMessage(
          "Starting interactive learning flow... This will help you comprehend the document through a multi-agent experience utilizing explainers, diagrams, quizzes, and flashcards.");

      // Send the start flow command to the backend
      print('Sending start flow command to initiate multi-agent learning path');

      // Tell the user it's loading
      chatController.setLoading(true);

      // Send the start flow command - added await here
      await chatController.sendMessage("start flow", isSystemCommand: true);

      // Log debug information
      print('Start studying flow command sent successfully');
    } catch (e) {
      print('Error starting study flow: $e');

      // Show error in the chat
      final ChatController chatController = Get.find<ChatController>();
      chatController.addSystemMessage(
          "There was an error starting the learning flow. Please try again or upload a different document.");
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

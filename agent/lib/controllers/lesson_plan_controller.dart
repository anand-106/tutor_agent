import 'package:get/get.dart';
import 'package:agent/models/lesson_plan.dart';
import 'package:agent/services/api_service.dart';
import 'package:agent/controllers/user_progress_controller.dart';
import 'package:flutter/material.dart';

class LessonPlanController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();
  final UserProgressController _userProgressController =
      Get.find<UserProgressController>();

  final Rx<LessonPlan?> currentLessonPlan = Rx<LessonPlan?>(null);
  final Rx<Curriculum?> currentCurriculum = Rx<Curriculum?>(null);
  final RxBool isGeneratingLessonPlan = false.obs;
  final RxBool isGeneratingCurriculum = false.obs;
  final RxString errorMessage = "".obs;

  Future<void> generateLessonPlan(String topic,
      {List<Map<String, dynamic>>? subtopics, int timeAvailable = 60}) async {
    try {
      isGeneratingLessonPlan.value = true;
      errorMessage.value = "";

      // Get the user's knowledge level for this topic
      final topicProgress =
          await _userProgressController.fetchTopicProgress(topic);
      final knowledgeLevel = topicProgress.level;

      // Generate the lesson plan
      final response = await _apiService.generateLessonPlan(
        _userProgressController.userId.value,
        topic,
        knowledgeLevel,
        subtopics: subtopics,
        timeAvailable: timeAvailable,
      );

      // Parse the response
      currentLessonPlan.value = LessonPlan.fromJson(response);

      Get.snackbar(
        'Success',
        'Lesson plan generated successfully',
        backgroundColor: Colors.green.withOpacity(0.1),
        colorText: Colors.white,
        duration: Duration(seconds: 2),
      );
    } catch (e) {
      errorMessage.value = "Failed to generate lesson plan: $e";
      Get.snackbar(
        'Error',
        errorMessage.value,
        backgroundColor: Colors.red.withOpacity(0.1),
        colorText: Colors.white,
        duration: Duration(seconds: 3),
      );
    } finally {
      isGeneratingLessonPlan.value = false;
    }
  }

  Future<void> generateCurriculum(List<String> topicNames,
      {int totalTimeAvailable = 600}) async {
    try {
      isGeneratingCurriculum.value = true;
      errorMessage.value = "";

      // Get the user's knowledge level for each topic
      final topics = <Map<String, dynamic>>[];
      for (final topicName in topicNames) {
        final topicProgress =
            await _userProgressController.fetchTopicProgress(topicName);
        topics.add({
          'name': topicName,
          'level': topicProgress.level,
        });
      }

      // Generate the curriculum
      final response = await _apiService.generateCurriculum(
        _userProgressController.userId.value,
        topics,
        totalTimeAvailable: totalTimeAvailable,
      );

      // Parse the response
      currentCurriculum.value = Curriculum.fromJson(response);

      Get.snackbar(
        'Success',
        'Curriculum generated successfully',
        backgroundColor: Colors.green.withOpacity(0.1),
        colorText: Colors.white,
        duration: Duration(seconds: 2),
      );
    } catch (e) {
      errorMessage.value = "Failed to generate curriculum: $e";
      Get.snackbar(
        'Error',
        errorMessage.value,
        backgroundColor: Colors.red.withOpacity(0.1),
        colorText: Colors.white,
        duration: Duration(seconds: 3),
      );
    } finally {
      isGeneratingCurriculum.value = false;
    }
  }

  void clearLessonPlan() {
    currentLessonPlan.value = null;
  }

  void clearCurriculum() {
    currentCurriculum.value = null;
  }
}

import 'package:get/get.dart';
import 'package:agent/models/user_progress.dart';
import 'package:agent/services/api_service.dart';
import 'package:flutter/material.dart';

class UserProgressController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();
  final RxString userId = "user1".obs; // Default user ID, can be changed
  final Rx<UserProgress?> userProgress = Rx<UserProgress?>(null);
  final Rx<LearningPattern?> learningPattern = Rx<LearningPattern?>(null);
  final RxMap<String, TopicProgress> topicProgress =
      <String, TopicProgress>{}.obs;
  final RxBool isLoading = false.obs;
  final RxBool hasError = false.obs;
  final RxString errorMessage = "".obs;

  @override
  void onInit() {
    super.onInit();
    fetchUserProgress();
  }

  void setUserId(String newUserId) {
    userId.value = newUserId;
    fetchUserProgress();
  }

  Future<void> fetchUserProgress() async {
    try {
      isLoading.value = true;
      hasError.value = false;
      errorMessage.value = "";

      final response = await _apiService.getUserKnowledgeSummary(userId.value);
      userProgress.value = UserProgress.fromJson(response);

      // Also fetch learning patterns
      await fetchLearningPatterns();

      Get.snackbar(
        'Success',
        'User progress loaded successfully',
        backgroundColor: Colors.green.withOpacity(0.1),
        colorText: Colors.white,
        duration: Duration(seconds: 2),
      );
    } catch (e) {
      hasError.value = true;
      errorMessage.value = "Failed to load user progress: $e";
      Get.snackbar(
        'Error',
        errorMessage.value,
        backgroundColor: Colors.red.withOpacity(0.1),
        colorText: Colors.white,
        duration: Duration(seconds: 3),
      );
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> fetchLearningPatterns() async {
    try {
      final response = await _apiService.getLearningPatterns(userId.value);

      // Check if response is valid
      if (response != null && response is Map<String, dynamic>) {
        // Ensure the response has the expected structure
        if (!response.containsKey('insights')) {
          response['insights'] = [];
        }
        if (!response.containsKey('interaction_counts')) {
          response['interaction_counts'] = {};
        }

        learningPattern.value = LearningPattern.fromJson(response);
      } else {
        // Create a default learning pattern if response is invalid
        learningPattern.value = LearningPattern(
          userId: userId.value,
          interactionCounts: {},
          studyRegularity: "none",
          insights: [],
        );
      }
    } catch (e) {
      print('Error fetching learning patterns: $e');
      // Create a default learning pattern on error
      learningPattern.value = LearningPattern(
        userId: userId.value,
        interactionCounts: {},
        studyRegularity: "none",
        insights: [],
      );
      // Don't show error snackbar for this, as it's secondary information
    }
  }

  Future<TopicProgress> fetchTopicProgress(String topic) async {
    try {
      // Check if we already have this topic's progress
      if (topicProgress.containsKey(topic)) {
        return topicProgress[topic]!;
      }

      final response = await _apiService.getTopicProgress(userId.value, topic);
      final progress = TopicProgress.fromJson(response);
      topicProgress[topic] = progress;
      return progress;
    } catch (e) {
      print('Error fetching topic progress: $e');
      // Return a default progress object
      return TopicProgress(
        name: topic,
        level: 0,
        lastUpdated: DateTime.now().toIso8601String(),
        status: 'not_started',
      );
    }
  }

  Future<void> trackQuizResult(
      String topic, int score, List<Map<String, dynamic>> questions) async {
    try {
      isLoading.value = true;
      await _apiService.trackUserInteraction(
        userId.value,
        'quiz_result',
        topic: topic,
        score: score,
        questions: questions,
      );

      // Refresh user progress after tracking
      await fetchUserProgress();

      // Also refresh this specific topic's progress
      await fetchTopicProgress(topic);
    } catch (e) {
      Get.snackbar(
        'Error',
        'Failed to track quiz result: $e',
        backgroundColor: Colors.red.withOpacity(0.1),
        colorText: Colors.white,
        duration: Duration(seconds: 3),
      );
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> trackStudySession(String topic, int durationMinutes) async {
    try {
      isLoading.value = true;
      await _apiService.trackUserInteraction(
        userId.value,
        'study_session',
        topic: topic,
        durationMinutes: durationMinutes,
      );

      // Refresh user progress after tracking
      await fetchUserProgress();

      // Also refresh this specific topic's progress
      await fetchTopicProgress(topic);
    } catch (e) {
      Get.snackbar(
        'Error',
        'Failed to track study session: $e',
        backgroundColor: Colors.red.withOpacity(0.1),
        colorText: Colors.white,
        duration: Duration(seconds: 3),
      );
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> trackFlashcardReview(
      String topic, int cardsReviewed, int correctRecalls) async {
    try {
      isLoading.value = true;
      await _apiService.trackUserInteraction(
        userId.value,
        'flashcard_review',
        topic: topic,
        cardsReviewed: cardsReviewed,
        correctRecalls: correctRecalls,
      );

      // Refresh user progress after tracking
      await fetchUserProgress();

      // Also refresh this specific topic's progress
      await fetchTopicProgress(topic);
    } catch (e) {
      Get.snackbar(
        'Error',
        'Failed to track flashcard review: $e',
        backgroundColor: Colors.red.withOpacity(0.1),
        colorText: Colors.white,
        duration: Duration(seconds: 3),
      );
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> trackTopicView(String topic, int viewDurationSeconds) async {
    try {
      await _apiService.trackUserInteraction(
        userId.value,
        'topic_view',
        topic: topic,
        viewDurationSeconds: viewDurationSeconds,
      );

      // Don't refresh everything for simple topic views to avoid too many API calls
      // Just refresh this specific topic's progress
      await fetchTopicProgress(topic);
    } catch (e) {
      print('Error tracking topic view: $e');
      // Don't show error snackbar for this, as it's a background operation
    }
  }
}

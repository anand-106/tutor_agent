import 'package:get/get.dart';
import 'package:agent/models/chat_message.dart';
import 'package:agent/services/api_service.dart';
import 'package:agent/controllers/user_progress_controller.dart';
import 'package:agent/controllers/lesson_plan_controller.dart';
import 'package:agent/models/lesson_plan.dart';
import 'dart:convert';

class ChatController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();
  final UserProgressController _userProgressController =
      Get.find<UserProgressController>();
  final RxList<ChatMessage> messages = <ChatMessage>[].obs;
  final RxBool isLoading = false.obs;
  final RxList<Map<String, dynamic>> pinnedFlashcards =
      <Map<String, dynamic>>[].obs;

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    // Add user message
    messages.add(ChatMessage(response: text, isUser: true));

    try {
      isLoading.value = true;

      // Get AI response with user ID
      final response = await _apiService.sendChatMessage(
        text,
        userId: _userProgressController.userId.value,
      );
      print('Received response: $response'); // Debug print

      if (response is Map<String, dynamic>) {
        // Check if there was an error
        if (response.containsKey('error')) {
          String errorMsg = 'There was an error processing your request.';
          if (response['error'] == 'rate_limit') {
            errorMsg =
                'The system is currently busy. Please try again in a moment.';
          } else if (response['error'] == 'communication') {
            errorMsg =
                'There was an error communicating with the server. Please check your connection.';
          }
          messages.add(ChatMessage(response: errorMsg, isUser: false));
          return;
        }

        // Check if the response contains a question
        if (response.containsKey('question') &&
            response.containsKey('has_question') &&
            response['has_question'] == true) {
          print('Handling question response: ${json.encode(response)}');

          messages.add(ChatMessage(
            response:
                response['response'] as String? ?? "Here's a question for you:",
            isUser: false,
            hasQuestion: true,
            question: response['question'] as Map<String, dynamic>,
          ));

          return;
        }

        // Check if the response contains a lesson plan
        if (response.containsKey('lesson_plan') &&
            response.containsKey('has_lesson_plan') &&
            response['has_lesson_plan'] == true) {
          print('Handling lesson plan response');

          // Save the lesson plan in the lesson plan controller
          final lessonPlanController = Get.find<LessonPlanController>();
          final lessonPlanData =
              response['lesson_plan'] as Map<String, dynamic>;
          lessonPlanController.currentLessonPlan.value =
              LessonPlan.fromJson(lessonPlanData);

          // If this is from a topic selection, inform the user
          String messageText = response['response'] as String? ??
              "I've created a lesson plan based on your selection.";

          messages.add(ChatMessage(
            response: messageText,
            isUser: false,
          ));

          // If this was not triggered by direct user action (like auto-generating after topic selection),
          // navigate to the lesson plan view
          if (response['is_from_topic_selection'] == true) {
            Get.toNamed('/lesson-plan');
          }

          return;
        }

        String messageText;
        if (response.containsKey('flashcards')) {
          // If it's a flashcard response, keep it as JSON
          messageText = json.encode(response);
        } else {
          messageText = response['response'] as String? ??
              "I'm not sure how to respond to that.";
        }

        final hasDiagram = response['has_diagram'] as bool? ?? false;
        final mermaidCode = response['mermaid_code'] as String?;
        final diagramType = response['diagram_type'] as String?;

        messages.add(ChatMessage(
          response: messageText,
          isUser: false,
          hasDiagram: hasDiagram,
          mermaidCode: mermaidCode,
          diagramType: diagramType,
        ));
      } else {
        messages.add(ChatMessage(response: response.toString(), isUser: false));
      }
    } catch (e) {
      print('Error in sendMessage: $e'); // Debug print
      Get.snackbar('Error', 'Failed to get response: $e');

      // Add error message to chat
      messages.add(ChatMessage(
          response:
              "I'm sorry, I encountered an error while processing your request. Please try again.",
          isUser: false));
    } finally {
      isLoading.value = false;
    }
  }

  void addSystemMessage(String text) {
    messages.add(ChatMessage(response: text, isUser: false));
  }

  void clearChat() {
    messages.clear();
  }

  void pinCard(Map<String, dynamic> card) {
    print('Attempting to pin card: ${json.encode(card)}'); // Debug print
    final index =
        pinnedFlashcards.indexWhere((pinned) => pinned['id'] == card['id']);
    if (index == -1) {
      // Card is not pinned, add it
      card['is_pinned'] = true;
      final cardCopy = Map<String, dynamic>.from(card);
      print('Adding new pinned card with ID: ${cardCopy['id']}'); // Debug print
      pinnedFlashcards.add(cardCopy);
      print(
          'Current pinned cards count: ${pinnedFlashcards.length}'); // Debug print
      print(
          'Pinned cards IDs: ${pinnedFlashcards.map((c) => c['id']).toList()}'); // Debug print
    } else {
      // Card is already pinned, update it
      print(
          'Updating existing pinned card at index $index with ID: ${card['id']}'); // Debug print
      pinnedFlashcards[index] = Map<String, dynamic>.from(card);
    }
  }

  void unpinCard(Map<String, dynamic> card) {
    print('Attempting to unpin card: ${json.encode(card)}'); // Debug print
    final index =
        pinnedFlashcards.indexWhere((pinned) => pinned['id'] == card['id']);
    if (index != -1) {
      print(
          'Removing card with ID: ${card['id']} from pinned cards'); // Debug print
      card['is_pinned'] = false;
      pinnedFlashcards.removeAt(index);
      print(
          'Current pinned cards count: ${pinnedFlashcards.length}'); // Debug print
      print(
          'Remaining pinned cards IDs: ${pinnedFlashcards.map((c) => c['id']).toList()}'); // Debug print
    } else {
      print(
          'Card with ID: ${card['id']} not found in pinned cards'); // Debug print
    }
  }

  void pinAllCards(List<Map<String, dynamic>> cards) {
    print('Attempting to pin all cards: ${cards.length}'); // Debug print
    for (var card in cards) {
      if (!card['is_pinned']) {
        card['is_pinned'] = true;
        final cardCopy = Map<String, dynamic>.from(card);
        if (!pinnedFlashcards.any((pinned) => pinned['id'] == cardCopy['id'])) {
          print(
              'Adding card with ID: ${cardCopy['id']} to pinned cards'); // Debug print
          pinnedFlashcards.add(cardCopy);
        }
      }
    }
    print(
        'Total pinned cards after pinning all: ${pinnedFlashcards.length}'); // Debug print
    print(
        'All pinned cards IDs: ${pinnedFlashcards.map((c) => c['id']).toList()}'); // Debug print
  }
}

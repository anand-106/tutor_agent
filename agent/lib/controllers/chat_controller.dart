import 'package:get/get.dart';
import 'package:agent/models/chat_message.dart';
import 'package:agent/services/api_service.dart';
import 'package:agent/controllers/user_progress_controller.dart';
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
        String messageText;
        if (response.containsKey('flashcards')) {
          // If it's a flashcard response, keep it as JSON
          messageText = json.encode(response);
        } else {
          messageText = response['response'] as String;
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

import 'package:get/get.dart';
import 'package:agent/models/chat_message.dart';
import 'package:agent/services/api_service.dart';

class ChatController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();
  final RxList<ChatMessage> messages = <ChatMessage>[].obs;
  final RxBool isLoading = false.obs;

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    // Add user message
    messages.add(ChatMessage(response: text, isUser: true));

    try {
      isLoading.value = true;

      // Get AI response
      final response = await _apiService.sendChatMessage(text);

      // Add AI response with diagram if present
      if (response is Map<String, dynamic>) {
        final messageText = response['response'] as String;
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
}

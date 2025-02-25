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
    messages.add(ChatMessage(text: text, isUser: true));

    try {
      isLoading.value = true;

      // Get AI response
      final response = await _apiService.sendChatMessage(text);

      // Add AI response
      messages.add(ChatMessage(text: response, isUser: false));
    } catch (e) {
      Get.snackbar('Error', 'Failed to get response: $e');
    } finally {
      isLoading.value = false;
    }
  }

  void clearChat() {
    messages.clear();
  }
}

import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:agent/controllers/chat_controller.dart';
import 'package:agent/widgets/chat_message_widget.dart';

class ChatWidget extends GetView<ChatController> {
  final TextEditingController textController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Chat messages
        Expanded(
          child: Obx(() => ListView.builder(
                itemCount: controller.messages.length,
                itemBuilder: (context, index) {
                  final message = controller.messages[index];
                  return ChatMessageWidget(message: message);
                },
              )),
        ),

        // Input area
        Padding(
          padding: EdgeInsets.all(8.0),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: textController,
                  decoration: InputDecoration(
                    hintText: 'Ask a question...',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
              SizedBox(width: 8),
              Obx(
                () => controller.isLoading.value
                    ? CircularProgressIndicator()
                    : IconButton(
                        icon: Icon(Icons.send),
                        onPressed: () {
                          if (textController.text.isNotEmpty) {
                            controller.sendMessage(textController.text);
                            textController.clear();
                          }
                        },
                      ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

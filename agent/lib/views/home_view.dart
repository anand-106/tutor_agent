import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:agent/controllers/chat_controller.dart';
import 'package:agent/controllers/document_controller.dart';
import 'package:agent/widgets/chat_widget.dart';
import 'package:agent/widgets/document_upload_widget.dart';

class HomeView extends GetView<ChatController> {
  final DocumentController documentController = Get.put(DocumentController());

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('AI Tutor'),
        actions: [
          IconButton(
            icon: Icon(Icons.delete),
            onPressed: controller.clearChat,
          ),
        ],
      ),
      body: Row(
        children: [
          // Document upload section
          Container(
            width: 300,
            child: DocumentUploadWidget(),
          ),

          // Vertical divider
          VerticalDivider(),

          // Chat section
          Expanded(
            child: ChatWidget(),
          ),
        ],
      ),
    );
  }
}

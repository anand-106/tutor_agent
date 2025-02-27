import 'package:flutter/material.dart';
import 'package:agent/models/chat_message.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:get/get.dart';
import 'package:agent/controllers/chat_controller.dart';
import 'package:agent/widgets/topic_item_widget.dart';
import 'package:agent/services/api_service.dart';

class ChatMessageWidget extends StatelessWidget {
  final ChatMessage message;
  final ChatController chatController = Get.find<ChatController>();

  ChatMessageWidget({required this.message});

  bool isTopicsMessage() {
    return message.text
        .startsWith("Here are the topics extracted from your document:");
  }

  Widget buildTopicsWidget(BuildContext context, Map<String, dynamic> topics) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
      ),
      margin: EdgeInsets.symmetric(vertical: 8),
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: topics.entries.map((entry) {
          if (entry.value is Map<String, dynamic>) {
            final content = entry.value as Map<String, dynamic>;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (content['subtopics'] != null)
                  ...content['subtopics'].map<Widget>((subtopic) {
                    return TopicItemWidget(
                      title: subtopic['title'] ?? '',
                      subtopics: subtopic['subtopics'],
                      chatController: chatController,
                    );
                  }).toList(),
              ],
            );
          }
          return SizedBox.shrink();
        }).toList(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Debug print
    print('Message text: ${message.text}');

    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.8,
        ),
        margin: EdgeInsets.symmetric(vertical: 8, horizontal: 16),
        padding: EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: message.isUser
              ? Theme.of(context).primaryColor.withOpacity(0.1)
              : Colors.grey[100],
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 5,
              offset: Offset(0, 2),
            ),
          ],
        ),
        child: message.isUser
            ? Text(
                message.text,
                style: GoogleFonts.inter(fontSize: 16),
              )
            : isTopicsMessage()
                ? FutureBuilder<Map<String, dynamic>>(
                    future: Get.find<ApiService>().getTopics(),
                    builder: (context, snapshot) {
                      if (snapshot.connectionState == ConnectionState.waiting) {
                        return CircularProgressIndicator();
                      }
                      if (snapshot.hasError) {
                        return Text('Error loading topics: ${snapshot.error}');
                      }
                      if (!snapshot.hasData) {
                        return Text('No topics available');
                      }
                      return buildTopicsWidget(context, snapshot.data!);
                    },
                  )
                : SingleChildScrollView(
                    child: MarkdownBody(
                      data: message.text,
                      selectable: true,
                      softLineBreak: true,
                      styleSheet: MarkdownStyleSheet(
                        h1: GoogleFonts.inter(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).primaryColor,
                        ),
                        h2: GoogleFonts.inter(
                          fontSize: 20,
                          fontWeight: FontWeight.w600,
                          color: Colors.black87,
                        ),
                        p: GoogleFonts.inter(
                          fontSize: 16,
                          color: Colors.black87,
                        ),
                        listBullet: GoogleFonts.inter(
                          fontSize: 16,
                          color: Theme.of(context).primaryColor,
                        ),
                        code: GoogleFonts.firaCode(
                          backgroundColor: Colors.grey[200],
                          fontSize: 14,
                        ),
                        codeblockDecoration: BoxDecoration(
                          color: Colors.grey[200],
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),
                  ),
      ),
    );
  }
}

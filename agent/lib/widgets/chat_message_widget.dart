import 'package:flutter/material.dart';
import 'package:agent/models/chat_message.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:get/get.dart';
import 'package:agent/controllers/chat_controller.dart';
import 'package:agent/widgets/topic_item_widget.dart';
import 'package:agent/services/api_service.dart';
import 'dart:convert';
import 'package:agent/widgets/quiz_widget.dart';

class ChatMessageWidget extends StatelessWidget {
  final ChatMessage message;
  final ChatController chatController = Get.find<ChatController>();

  ChatMessageWidget({required this.message});

  bool isTopicsMessage() {
    return message.text
        .startsWith("Here are the topics extracted from your document:");
  }

  @override
  Widget build(BuildContext context) {
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
            : _buildAIResponse(context, message.text),
      ),
    );
  }

  Widget _buildAIResponse(BuildContext context, String text) {
    // First check if it's a topics message
    if (isTopicsMessage()) {
      return FutureBuilder<Map<String, dynamic>>(
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
      );
    }

    // Then try to parse as JSON for quiz
    try {
      // Clean up the text to handle markdown code blocks
      String jsonText = text;
      if (text.contains("```json")) {
        jsonText = text.split("```json")[1].split("```")[0].trim();
      }

      final data = json.decode(jsonText);
      if (data is Map<String, dynamic> &&
          data.containsKey('questions') &&
          data.containsKey('topic')) {
        return QuizWidget(quizData: data);
      }
    } catch (e) {
      print('Error parsing quiz JSON: $e');
      // Not JSON or wrong format, continue to markdown
    }

    // Default to markdown
    return SingleChildScrollView(
      child: MarkdownBody(
        data: text,
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
    );
  }

  Widget buildTopicsWidget(BuildContext context, Map<String, dynamic> topics) {
    // Check for error state in topics
    if (topics.values.any((value) {
      if (value is Map<String, dynamic>) {
        return value['content']?.toString().contains('429') ?? false;
      }
      return false;
    })) {
      return Container(
        padding: EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.orange[50],
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.orange[200]!),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.warning_amber_rounded, color: Colors.orange),
                SizedBox(width: 8),
                Text(
                  'Topics are being processed',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.orange[800],
                  ),
                ),
              ],
            ),
            SizedBox(height: 12),
            Text(
              'Please wait a moment and try again. The system is currently processing your document.',
              style: TextStyle(color: Colors.orange[900]),
            ),
            SizedBox(height: 16),
            ElevatedButton.icon(
              icon: Icon(Icons.refresh),
              label: Text('Retry Loading Topics'),
              onPressed: () {
                chatController.sendMessage("Show me the topics");
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.orange[100],
                foregroundColor: Colors.orange[900],
              ),
            ),
          ],
        ),
      );
    }

    // Normal topics display
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
        children: [
          Text(
            'Document Topics',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Theme.of(context).primaryColor,
            ),
          ),
          SizedBox(height: 16),
          ...topics.entries.map((entry) {
            if (entry.value is Map<String, dynamic>) {
              final content = entry.value as Map<String, dynamic>;
              if (content['subtopics'] == null ||
                  (content['subtopics'] as List).isEmpty) {
                return Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text(
                    'No topics available yet. Please try again in a moment.',
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                );
              }
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
        ],
      ),
    );
  }
}

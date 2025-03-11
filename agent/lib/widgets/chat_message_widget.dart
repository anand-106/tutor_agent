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
import 'package:agent/widgets/mermaid_diagram.dart';
import 'dart:ui';
import 'package:agent/controllers/document_controller.dart';

class ChatMessageWidget extends StatelessWidget {
  final ChatMessage message;
  final ChatController chatController = Get.find<ChatController>();
  final DocumentController documentController = Get.find<DocumentController>();

  ChatMessageWidget({required this.message});

  bool isTopicsMessage() {
    return message.response
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
        child: ClipRRect(
          borderRadius: BorderRadius.circular(20),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
            child: Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: message.isUser
                    ? Theme.of(context).primaryColor.withOpacity(0.15)
                    : Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: message.isUser
                      ? Theme.of(context).primaryColor.withOpacity(0.2)
                      : Colors.white.withOpacity(0.08),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.2),
                    blurRadius: 10,
                    offset: Offset(0, 4),
                  ),
                ],
              ),
              child: message.isUser
                  ? Text(
                      message.response,
                      style: GoogleFonts.inter(
                        fontSize: 16,
                        color: Colors.white.withOpacity(0.9),
                      ),
                    )
                  : _buildAIResponse(context, message.response),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildAIResponse(BuildContext context, String text) {
    if (isTopicsMessage()) {
      return Obx(() {
        final topicsData = documentController.topics.value;
        final status = topicsData['status'] as String;

        switch (status) {
          case 'loading':
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(
                    valueColor: AlwaysStoppedAnimation<Color>(
                      Theme.of(context).primaryColor,
                    ),
                  ),
                  SizedBox(height: 16),
                  Text(
                    'Loading topics...',
                    style: GoogleFonts.inter(
                      color: Colors.white.withOpacity(0.7),
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            );

          case 'error':
            return Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.red.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: Colors.red.withOpacity(0.2),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.error_outline, color: Colors.red[300]),
                      SizedBox(width: 8),
                      Text(
                        'Error Loading Topics',
                        style: GoogleFonts.inter(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.red[300],
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 8),
                  Text(
                    topicsData['message'] ?? 'An unknown error occurred',
                    style: GoogleFonts.inter(
                      color: Colors.red[200],
                      fontSize: 14,
                    ),
                  ),
                  SizedBox(height: 16),
                  ElevatedButton.icon(
                    icon: Icon(Icons.refresh),
                    label: Text('Retry'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red.withOpacity(0.2),
                      foregroundColor: Colors.red[300],
                    ),
                    onPressed: () => documentController.refreshTopics(),
                  ),
                ],
              ),
            );

          case 'empty':
            return Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: Colors.white.withOpacity(0.08),
                ),
              ),
              child: Column(
                children: [
                  Icon(
                    Icons.topic_outlined,
                    size: 48,
                    color: Colors.white.withOpacity(0.3),
                  ),
                  SizedBox(height: 16),
                  Text(
                    'No topics available yet',
                    style: GoogleFonts.inter(
                      color: Colors.white.withOpacity(0.7),
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  Text(
                    'Upload a document to see topics',
                    style: GoogleFonts.inter(
                      color: Colors.white.withOpacity(0.5),
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            );

          case 'success':
            return buildTopicsWidget(context, topicsData);

          default:
            return Text(
              'Unknown state',
              style: GoogleFonts.inter(color: Colors.white70),
            );
        }
      });
    }

    // Check if this is a quiz response
    if (text.contains('```json')) {
      try {
        // Extract JSON content from code blocks
        RegExp regExp = RegExp(r'```json\s*([\s\S]*?)\s*```');
        Match? match = regExp.firstMatch(text);

        if (match != null) {
          String jsonText = match.group(1)?.trim() ?? '';
          print('Found quiz JSON: $jsonText'); // Debug print

          try {
            // Clean up the JSON text
            jsonText = jsonText
                .replaceAll(RegExp(r',(\s*[}\]])', multiLine: true), r'$1')
                .replaceAll(RegExp(r'[\n\r]'), '')
                .trim();

            final data = json.decode(jsonText);
            print('Parsed quiz data: $data'); // Debug print

            if (data is Map<String, dynamic> &&
                data.containsKey('questions') &&
                data.containsKey('topic')) {
              print('Creating quiz widget with data: $data'); // Debug print
              return QuizWidget(quizData: data);
            } else {
              print('Invalid quiz data format: $data'); // Debug print
            }
          } catch (e) {
            print('Error parsing quiz JSON: $e'); // Debug print
          }
        } else {
          print('No JSON content found in markdown blocks'); // Debug print
        }
      } catch (e) {
        print('Error processing quiz response: $e'); // Debug print
      }
    }

    // If the message has a diagram, show both the text and diagram
    if (message.hasDiagram && message.mermaidCode != null) {
      print('Rendering diagram with code: ${message.mermaidCode}'); // Debug log

      // Extract explanation text (everything before the Mermaid code block)
      String explanation = message.response.split('```mermaid').first.trim();

      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (explanation.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 16.0),
              child: MarkdownBody(data: explanation),
            ),
          Container(
            margin: const EdgeInsets.symmetric(vertical: 8.0),
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.8,
              maxHeight: 400,
            ),
            decoration: BoxDecoration(
              color: Colors.black12,
              borderRadius: BorderRadius.circular(8),
            ),
            child: MermaidDiagram(
              diagramCode: message.mermaidCode!,
              width: MediaQuery.of(context).size.width * 0.8,
              height: 400,
            ),
          ),
        ],
      );
    }

    // If not a diagram or quiz, render as markdown
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
            color: Colors.white.withOpacity(0.9),
          ),
          p: GoogleFonts.inter(
            fontSize: 16,
            color: Colors.white.withOpacity(0.9),
          ),
          listBullet: GoogleFonts.inter(
            fontSize: 16,
            color: Theme.of(context).primaryColor,
          ),
          code: GoogleFonts.firaCode(
            backgroundColor: Colors.black.withOpacity(0.3),
            color: Colors.white.withOpacity(0.9),
            fontSize: 14,
          ),
          codeblockDecoration: BoxDecoration(
            color: Colors.black.withOpacity(0.3),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: Colors.white.withOpacity(0.1),
            ),
          ),
        ),
      ),
    );
  }

  Widget buildTopicsWidget(BuildContext context, Map<String, dynamic> topics) {
    final topicsList = topics['topics'] as List?;

    if (topicsList == null || topicsList.isEmpty) {
      return Container(
        padding: EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: Colors.white.withOpacity(0.08),
          ),
        ),
        child: Column(
          children: [
            Icon(
              Icons.topic_outlined,
              size: 48,
              color: Colors.white.withOpacity(0.3),
            ),
            SizedBox(height: 16),
            Text(
              'No topics found',
              style: GoogleFonts.inter(
                color: Colors.white.withOpacity(0.7),
                fontSize: 16,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Colors.white.withOpacity(0.08),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      margin: EdgeInsets.symmetric(vertical: 8),
      padding: EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Document Topics',
            style: GoogleFonts.inter(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Theme.of(context).primaryColor,
            ),
          ),
          SizedBox(height: 16),
          ...topicsList.map((topic) {
            if (topic is Map<String, dynamic>) {
              return TopicItemWidget(
                title: topic['title'] ?? '',
                subtopics: topic['subtopics'],
                chatController: chatController,
              );
            }
            return SizedBox.shrink();
          }).toList(),
        ],
      ),
    );
  }
}

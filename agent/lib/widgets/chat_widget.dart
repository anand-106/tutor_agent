import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:agent/controllers/chat_controller.dart';
import 'package:agent/widgets/chat_message_widget.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:agent/controllers/document_controller.dart';

class ChatWidget extends GetView<ChatController> {
  final TextEditingController textController = TextEditingController();
  final DocumentController documentController = Get.find<DocumentController>();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.all(24),
      child: Column(
        children: [
          // Topics Card
          Container(
            constraints: BoxConstraints(maxHeight: 300),
            margin: EdgeInsets.only(bottom: 24),
            decoration: BoxDecoration(
              color: Color(0xFF1E1E1E),
              borderRadius: BorderRadius.circular(20),
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
            child: Obx(() {
              final topicsData = documentController.topics.value;
              final status = topicsData['status'] as String? ?? 'empty';
              final topicsList = topicsData['topics'] as List? ?? [];

              print('Building UI with topics: $topicsList'); // Debug print

              if (status == 'loading') {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
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
              }

              if (status == 'error') {
                return Padding(
                  padding: EdgeInsets.all(24),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.error_outline,
                        color: Colors.red[300],
                        size: 48,
                      ),
                      SizedBox(height: 16),
                      Text(
                        'Error loading topics',
                        style: GoogleFonts.inter(
                          color: Colors.red[300],
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      SizedBox(height: 8),
                      Text(
                        topicsData['message']?.toString() ??
                            'Unknown error occurred',
                        textAlign: TextAlign.center,
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
              }

              if (status == 'empty' || topicsList.isEmpty) {
                return Padding(
                  padding: EdgeInsets.all(24),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.topic_outlined,
                        size: 48,
                        color: Colors.white.withOpacity(0.3),
                      ),
                      SizedBox(height: 16),
                      Text(
                        'No topics available',
                        style: GoogleFonts.inter(
                          color: Colors.white.withOpacity(0.7),
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      Text(
                        'Upload a document to start studying',
                        style: GoogleFonts.inter(
                          color: Colors.white.withOpacity(0.5),
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                );
              }

              return SingleChildScrollView(
                child: Theme(
                  data: Theme.of(context).copyWith(
                    dividerColor: Colors.transparent,
                    listTileTheme: ListTileThemeData(
                      dense: true,
                      horizontalTitleGap: 0,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Padding(
                        padding: EdgeInsets.all(16),
                        child: Text(
                          'Document Topics',
                          style: GoogleFonts.inter(
                            color: Colors.white,
                            fontSize: 20,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      ...topicsList.map((topic) {
                        return _buildTopicTile(topic, context);
                      }).toList(),
                    ],
                  ),
                ),
              );
            }),
          ),

          // Chat messages
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: Color(0xFF1E1E1E),
                borderRadius: BorderRadius.circular(20),
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
              child: Obx(
                () => ListView.builder(
                  padding: EdgeInsets.all(20),
                  itemCount: controller.messages.length,
                  itemBuilder: (context, index) {
                    final message = controller.messages[index];
                    return ChatMessageWidget(message: message);
                  },
                ),
              ),
            ),
          ),

          // Input area
          Container(
            margin: EdgeInsets.only(top: 24),
            padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            decoration: BoxDecoration(
              color: Color(0xFF1E1E1E),
              borderRadius: BorderRadius.circular(20),
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
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: textController,
                    style: GoogleFonts.inter(
                      color: Colors.white,
                      fontSize: 16,
                    ),
                    decoration: InputDecoration(
                      hintText: 'Ask a question...',
                      hintStyle: GoogleFonts.inter(
                        color: Colors.white.withOpacity(0.4),
                        fontSize: 16,
                      ),
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.symmetric(horizontal: 16),
                    ),
                    onSubmitted: (text) {
                      if (text.isNotEmpty) {
                        controller.sendMessage(text);
                        textController.clear();
                      }
                    },
                  ),
                ),
                SizedBox(width: 16),
                Obx(
                  () => controller.isLoading.value
                      ? Container(
                          width: 24,
                          height: 24,
                          padding: EdgeInsets.all(2),
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(
                              Theme.of(context).primaryColor,
                            ),
                          ),
                        )
                      : Material(
                          color: Theme.of(context).primaryColor,
                          borderRadius: BorderRadius.circular(12),
                          child: InkWell(
                            borderRadius: BorderRadius.circular(12),
                            onTap: () {
                              if (textController.text.isNotEmpty) {
                                controller.sendMessage(textController.text);
                                textController.clear();
                              }
                            },
                            child: Container(
                              padding: EdgeInsets.all(12),
                              child: Icon(
                                Icons.send_rounded,
                                color: Colors.white,
                                size: 20,
                              ),
                            ),
                          ),
                        ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopicTile(Map<String, dynamic> topic, BuildContext context) {
    final String title = topic['title']?.toString() ?? '';
    final String content = topic['content']?.toString() ?? '';
    final List<dynamic> rawSubtopics = topic['subtopics'] ?? [];

    final List<Map<String, dynamic>> subtopics = rawSubtopics.map((subtopic) {
      if (subtopic is Map) {
        return Map<String, dynamic>.from(subtopic);
      }
      return <String, dynamic>{};
    }).toList();

    return Container(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Colors.white.withOpacity(0.08),
        ),
      ),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: GoogleFonts.inter(
                  color: Colors.white.withOpacity(0.9),
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                ),
              ),
              if (content.isNotEmpty)
                Padding(
                  padding: EdgeInsets.only(top: 4),
                  child: Text(
                    content,
                    style: GoogleFonts.inter(
                      color: Colors.white.withOpacity(0.5),
                      fontSize: 13,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
            ],
          ),
          trailing: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextButton(
                onPressed: () {
                  controller.sendMessage('Tell me about $title');
                },
                child: Text(
                  'Study',
                  style: GoogleFonts.inter(
                    color: Theme.of(context).primaryColor,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                style: TextButton.styleFrom(
                  backgroundColor:
                      Theme.of(context).primaryColor.withOpacity(0.1),
                  padding: EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
              SizedBox(width: 8),
              Icon(
                Icons.expand_more,
                color: Colors.white.withOpacity(0.5),
              ),
            ],
          ),
          children: subtopics.isNotEmpty
              ? subtopics.map((subtopic) {
                  return Padding(
                    padding: EdgeInsets.only(left: 16.0),
                    child: _buildTopicTile(subtopic, context),
                  );
                }).toList()
              : [],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:agent/controllers/document_controller.dart';
import 'package:agent/controllers/chat_controller.dart';
import 'package:agent/controllers/user_progress_controller.dart';
import 'package:agent/controllers/home_view_controller.dart';

class TopicsTab extends StatelessWidget {
  final DocumentController documentController = Get.find<DocumentController>();
  final ChatController chatController = Get.find<ChatController>();
  final UserProgressController userProgressController =
      Get.find<UserProgressController>();
  final HomeViewController homeViewController = Get.find<HomeViewController>();

  TopicsTab({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.all(16),
      child: Obx(() {
        final topicsData = documentController.topics.value;

        if (topicsData['status'] == 'loading') {
          return Center(
            child: CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(
                Theme.of(context).primaryColor,
              ),
            ),
          );
        }

        if (topicsData['status'] == 'error') {
          return Center(
            child: Text(
              topicsData['message'] ?? 'Error loading topics',
              style: GoogleFonts.inter(
                color: Colors.red.withOpacity(0.8),
              ),
            ),
          );
        }

        final topics = topicsData['topics'] as List;

        if (topics.isEmpty) {
          return Center(
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
                    color: Colors.white.withOpacity(0.5),
                  ),
                ),
                SizedBox(height: 8),
                Text(
                  'Upload a document to see topics',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.inter(
                    color: Colors.white.withOpacity(0.3),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          );
        }

        return ListView.builder(
          itemCount: topics.length,
          itemBuilder: (context, index) {
            final topic = topics[index];
            return Container(
              margin: EdgeInsets.only(bottom: 12),
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).primaryColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: Theme.of(context).primaryColor.withOpacity(0.2),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          topic['title'] ?? 'Untitled Topic',
                          style: GoogleFonts.inter(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                      ),
                      ElevatedButton.icon(
                        icon: Icon(Icons.school, size: 16),
                        label: Text('Study'),
                        onPressed: () {
                          // Implement study functionality
                          _studyTopic(topic['title'], topic['content']);
                        },
                        style: ElevatedButton.styleFrom(
                          padding: EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 8,
                          ),
                          textStyle: GoogleFonts.inter(
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                  if (topic['content'] != null) ...[
                    SizedBox(height: 8),
                    Text(
                      topic['content'],
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        color: Colors.white.withOpacity(0.7),
                      ),
                    ),
                  ],
                  if (topic['subtopics'] != null) ...[
                    SizedBox(height: 12),
                    ...List<Widget>.from(
                      (topic['subtopics'] as List).map(
                        (subtopic) => _buildSubtopic(context, subtopic),
                      ),
                    ),
                  ],
                ],
              ),
            );
          },
        );
      }),
    );
  }

  Widget _buildSubtopic(BuildContext context, dynamic subtopic) {
    if (subtopic is Map) {
      return Container(
        margin: EdgeInsets.only(left: 16),
        child: Stack(
          children: [
            // Vertical connection line
            Positioned(
              left: 2,
              top: 0,
              bottom: 0,
              width: 2,
              child: Container(
                color: Theme.of(context).primaryColor.withOpacity(0.3),
              ),
            ),
            // Horizontal connection line
            Positioned(
              left: 2,
              top: 12,
              width: 12,
              height: 2,
              child: Container(
                color: Theme.of(context).primaryColor.withOpacity(0.3),
              ),
            ),
            Padding(
              padding: EdgeInsets.only(
                left: 24,
                bottom: 12,
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          subtopic['title'] ?? '',
                          style: GoogleFonts.inter(
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                            color: Colors.white.withOpacity(0.9),
                          ),
                        ),
                        if (subtopic['content'] != null) ...[
                          SizedBox(height: 4),
                          Text(
                            subtopic['content'],
                            style: GoogleFonts.inter(
                              fontSize: 12,
                              color: Colors.white.withOpacity(0.7),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  ElevatedButton.icon(
                    icon: Icon(Icons.school, size: 14),
                    label: Text('Study'),
                    onPressed: () {
                      // Implement study functionality for map subtopic
                      _studyTopic(subtopic['title'], subtopic['content']);
                    },
                    style: ElevatedButton.styleFrom(
                      padding: EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      textStyle: GoogleFonts.inter(
                        fontSize: 11,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    } else {
      return Container(
        margin: EdgeInsets.only(left: 16),
        child: Stack(
          children: [
            // Vertical connection line
            Positioned(
              left: 2,
              top: 0,
              bottom: 0,
              width: 2,
              child: Container(
                color: Theme.of(context).primaryColor.withOpacity(0.3),
              ),
            ),
            // Horizontal connection line
            Positioned(
              left: 2,
              top: 12,
              width: 12,
              height: 2,
              child: Container(
                color: Theme.of(context).primaryColor.withOpacity(0.3),
              ),
            ),
            Padding(
              padding: EdgeInsets.only(
                left: 24,
                bottom: 12,
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      subtopic.toString(),
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        color: Colors.white.withOpacity(0.7),
                      ),
                    ),
                  ),
                  ElevatedButton.icon(
                    icon: Icon(Icons.school, size: 14),
                    label: Text('Study'),
                    onPressed: () {
                      // Implement study functionality for string subtopic
                      _studyTopic(subtopic.toString(), null);
                    },
                    style: ElevatedButton.styleFrom(
                      padding: EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      textStyle: GoogleFonts.inter(
                        fontSize: 11,
                        fontWeight: FontWeight.w500,
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
  }

  void _studyTopic(String topicTitle, String? topicContent) {
    // Track the study session in user progress
    userProgressController.trackStudySession(
        topicTitle, 15); // Default 15 minutes session

    // Create a study request message
    String studyRequest = "Help me study about $topicTitle.";
    if (topicContent != null && topicContent.isNotEmpty) {
      studyRequest += " Here's what I know: $topicContent";
    }

    // Send the study request to the chat
    chatController.sendMessage(studyRequest);

    // Close the side panel
    homeViewController.closeSidePanel();

    // Show a snackbar to confirm
    Get.snackbar(
      'Study Session Started',
      'Now studying: $topicTitle',
      backgroundColor: Colors.green.withOpacity(0.1),
      colorText: Colors.white,
      duration: Duration(seconds: 2),
    );
  }
}

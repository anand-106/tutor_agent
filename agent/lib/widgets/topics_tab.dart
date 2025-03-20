import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:agent/controllers/document_controller.dart';
import 'package:agent/controllers/chat_controller.dart';
import 'package:agent/controllers/lesson_plan_controller.dart';
import 'package:agent/views/lesson_plan_view.dart';

class TopicsTab extends StatelessWidget {
  final DocumentController documentController = Get.find<DocumentController>();
  final ChatController chatController = Get.find<ChatController>();
  final LessonPlanController lessonPlanController =
      Get.find<LessonPlanController>();

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
                          _studyTopic(topic['title'], topic['content'],
                              subtopics: topic['subtopics']);
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

  Future<void> _studyTopic(String title, String? content,
      {List<dynamic>? subtopics}) async {
    // Show dialog to ask if user wants to generate a lesson plan
    Get.dialog(
      AlertDialog(
        backgroundColor: Color(0xFF1A1A1A),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(
            color: Colors.white.withOpacity(0.1),
          ),
        ),
        title: Text(
          'Study $title',
          style: GoogleFonts.inter(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'How would you like to study this topic?',
              style: GoogleFonts.inter(
                color: Colors.white.withOpacity(0.8),
              ),
            ),
            SizedBox(height: 16),
            Row(
              children: [
                Icon(Icons.timer,
                    color: Colors.white.withOpacity(0.6), size: 20),
                SizedBox(width: 8),
                Text(
                  'Select study time (for lesson plan):',
                  style: GoogleFonts.inter(
                    color: Colors.white.withOpacity(0.8),
                  ),
                ),
              ],
            ),
            SizedBox(height: 8),
            _buildTimeSelectionChips(),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: Text(
              'Cancel',
              style: GoogleFonts.inter(
                color: Colors.white.withOpacity(0.6),
              ),
            ),
          ),
          TextButton(
            onPressed: () async {
              // Show loading indicator inside dialog
              Get.dialog(
                Dialog(
                  backgroundColor: Colors.transparent,
                  elevation: 0,
                  child: Center(
                    child: Container(
                      padding: EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: Color(0xFF1A1A1A),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          CircularProgressIndicator(),
                          SizedBox(height: 16),
                          Text(
                            'Starting study session...',
                            style: GoogleFonts.inter(
                              color: Colors.white,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                barrierDismissible: false,
              );

              // Close the selection dialog
              Get.back();

              // Get the document controller and call studyTopic
              final documentController = Get.find<DocumentController>();
              await documentController.studyTopic(title);

              // Close the loading dialog
              Get.back();
            },
            child: Text(
              'Direct Study',
              style: GoogleFonts.inter(
                color: Get.theme.primaryColor,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          ElevatedButton(
            onPressed: () {
              Get.back();
              _generateLessonPlan(title, subtopics);
            },
            child: Text(
              'Generate Plan',
              style: GoogleFonts.inter(
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }

  final RxInt _selectedTime = 30.obs;

  Widget _buildTimeSelectionChips() {
    return Obx(() => Wrap(
          spacing: 8,
          children: [15, 30, 45, 60, 90, 120].map((time) {
            return ChoiceChip(
              label: Text(
                '$time min',
                style: GoogleFonts.inter(
                  color: _selectedTime.value == time
                      ? Colors.white
                      : Colors.white.withOpacity(0.7),
                  fontSize: 12,
                ),
              ),
              selected: _selectedTime.value == time,
              onSelected: (selected) {
                if (selected) {
                  _selectedTime.value = time;
                }
              },
              backgroundColor: Colors.white.withOpacity(0.05),
              selectedColor: Get.theme.primaryColor,
            );
          }).toList(),
        ));
  }

  void _generateLessonPlan(String topic, List<dynamic>? subtopicsList) async {
    // Convert subtopics to the format expected by the lesson plan controller
    List<Map<String, dynamic>>? subtopics;
    if (subtopicsList != null && subtopicsList.isNotEmpty) {
      subtopics = subtopicsList.map((subtopic) {
        if (subtopic is Map) {
          return {
            'name': subtopic['title'] ?? '',
            'level': 0.0, // Default level, will be updated by the controller
          };
        }
        return {'name': subtopic.toString(), 'level': 0.0};
      }).toList();
    }

    // Generate the lesson plan
    await lessonPlanController.generateLessonPlan(
      topic,
      subtopics: subtopics,
      timeAvailable: _selectedTime.value,
    );

    // Navigate to the lesson plan view
    Get.to(() => LessonPlanView());
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
                      _studyTopic(
                        subtopic['title'] ?? 'Subtopic',
                        subtopic['content'],
                      );
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
                      _studyTopic(
                        subtopic.toString(),
                        null,
                      );
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
}

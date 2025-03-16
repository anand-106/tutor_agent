import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:agent/controllers/lesson_plan_controller.dart';
import 'package:agent/models/lesson_plan.dart';

class LessonPlanView extends StatelessWidget {
  final LessonPlanController _lessonPlanController =
      Get.find<LessonPlanController>();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF121212),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          'Lesson Plan',
          style: GoogleFonts.inter(
            color: Colors.white,
            fontWeight: FontWeight.w600,
          ),
        ),
        flexibleSpace: Container(
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.05),
            border: Border(
              bottom: BorderSide(
                color: Colors.white.withOpacity(0.1),
              ),
            ),
          ),
        ),
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFF1A1A1A),
              Color(0xFF121212),
            ],
          ),
        ),
        child: Obx(() {
          if (_lessonPlanController.isGeneratingLessonPlan.value) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text(
                    'Generating Lesson Plan...',
                    style: GoogleFonts.inter(
                      color: Colors.white,
                      fontSize: 16,
                    ),
                  ),
                ],
              ),
            );
          }

          if (_lessonPlanController.errorMessage.value.isNotEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, color: Colors.red, size: 48),
                  SizedBox(height: 16),
                  Text(
                    'Error',
                    style: GoogleFonts.inter(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    _lessonPlanController.errorMessage.value,
                    style: GoogleFonts.inter(
                      color: Colors.white70,
                      fontSize: 16,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            );
          }

          final lessonPlan = _lessonPlanController.currentLessonPlan.value;
          if (lessonPlan == null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.school_outlined, color: Colors.white54, size: 64),
                  SizedBox(height: 16),
                  Text(
                    'No Lesson Plan Available',
                    style: GoogleFonts.inter(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Generate a lesson plan from a topic first',
                    style: GoogleFonts.inter(
                      color: Colors.white70,
                      fontSize: 16,
                    ),
                  ),
                  SizedBox(height: 24),
                  ElevatedButton.icon(
                    icon: Icon(Icons.add),
                    label: Text('Generate Sample Lesson Plan'),
                    onPressed: () {
                      _lessonPlanController.generateLessonPlan('Sample Topic');
                    },
                  ),
                ],
              ),
            );
          }

          return SingleChildScrollView(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildHeader(lessonPlan, context),
                SizedBox(height: 24),
                _buildLearningObjectives(lessonPlan, context),
                SizedBox(height: 24),
                _buildActivities(lessonPlan, context),
                SizedBox(height: 24),
                _buildAssessment(lessonPlan, context),
                SizedBox(height: 24),
                _buildNextSteps(lessonPlan, context),
              ],
            ),
          );
        }),
      ),
    );
  }

  Widget _buildHeader(LessonPlan lessonPlan, BuildContext context) {
    return Card(
      color: Colors.white.withOpacity(0.05),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    lessonPlan.title,
                    style: GoogleFonts.inter(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Chip(
                  label: Text(
                    lessonPlan.knowledgeLevel.toUpperCase(),
                    style: GoogleFonts.inter(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                  backgroundColor:
                      _getKnowledgeLevelColor(lessonPlan.knowledgeLevel),
                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 0),
                ),
              ],
            ),
            SizedBox(height: 8),
            Text(
              lessonPlan.description,
              style: GoogleFonts.inter(
                color: Colors.white70,
                fontSize: 16,
              ),
            ),
            SizedBox(height: 16),
            Row(
              children: [
                Icon(Icons.access_time, color: Colors.white54, size: 20),
                SizedBox(width: 8),
                Text(
                  '${lessonPlan.durationMinutes} minutes',
                  style: GoogleFonts.inter(
                    color: Colors.white70,
                    fontSize: 14,
                  ),
                ),
                SizedBox(width: 16),
                Icon(Icons.topic, color: Colors.white54, size: 20),
                SizedBox(width: 8),
                Text(
                  lessonPlan.topic,
                  style: GoogleFonts.inter(
                    color: Colors.white70,
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLearningObjectives(LessonPlan lessonPlan, BuildContext context) {
    return Card(
      color: Colors.white.withOpacity(0.05),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.lightbulb_outline,
                    color: Theme.of(context).primaryColor),
                SizedBox(width: 8),
                Text(
                  'Learning Objectives',
                  style: GoogleFonts.inter(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            SizedBox(height: 16),
            ...lessonPlan.learningObjectives.map((objective) => Padding(
                  padding: EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.check_circle_outline,
                          color: Colors.white54, size: 20),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          objective,
                          style: GoogleFonts.inter(
                            color: Colors.white70,
                            fontSize: 16,
                          ),
                        ),
                      ),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Widget _buildActivities(LessonPlan lessonPlan, BuildContext context) {
    return Card(
      color: Colors.white.withOpacity(0.05),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.play_circle_outline,
                    color: Theme.of(context).primaryColor),
                SizedBox(width: 8),
                Text(
                  'Activities',
                  style: GoogleFonts.inter(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            SizedBox(height: 16),
            ...lessonPlan.activities
                .map((activity) => _buildActivityCard(activity, context)),
          ],
        ),
      ),
    );
  }

  Widget _buildActivityCard(LessonActivity activity, BuildContext context) {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: Colors.white.withOpacity(0.1),
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
                  activity.title,
                  style: GoogleFonts.inter(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              Chip(
                label: Text(
                  '${activity.durationMinutes} min',
                  style: GoogleFonts.inter(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
                backgroundColor:
                    Theme.of(context).primaryColor.withOpacity(0.3),
                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 0),
              ),
            ],
          ),
          SizedBox(height: 4),
          Text(
            activity.type.toUpperCase(),
            style: GoogleFonts.inter(
              color: Theme.of(context).primaryColor,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 8),
          Text(
            activity.description,
            style: GoogleFonts.inter(
              color: Colors.white70,
              fontSize: 14,
            ),
          ),
          if (activity.resources.isNotEmpty) ...[
            SizedBox(height: 12),
            Text(
              'Resources:',
              style: GoogleFonts.inter(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 8),
            ...activity.resources.map((resource) => Padding(
                  padding: EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(_getResourceIcon(resource.type),
                          color: Colors.white54, size: 16),
                      SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              resource.title,
                              style: GoogleFonts.inter(
                                color: Colors.white,
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            Text(
                              resource.description,
                              style: GoogleFonts.inter(
                                color: Colors.white70,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                )),
          ],
        ],
      ),
    );
  }

  Widget _buildAssessment(LessonPlan lessonPlan, BuildContext context) {
    return Card(
      color: Colors.white.withOpacity(0.05),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.assignment_outlined,
                    color: Theme.of(context).primaryColor),
                SizedBox(width: 8),
                Text(
                  'Assessment',
                  style: GoogleFonts.inter(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            SizedBox(height: 16),
            Row(
              children: [
                Chip(
                  label: Text(
                    lessonPlan.assessment.type.toUpperCase(),
                    style: GoogleFonts.inter(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                  backgroundColor:
                      Theme.of(context).primaryColor.withOpacity(0.3),
                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 0),
                ),
              ],
            ),
            SizedBox(height: 8),
            Text(
              lessonPlan.assessment.description,
              style: GoogleFonts.inter(
                color: Colors.white70,
                fontSize: 16,
              ),
            ),
            SizedBox(height: 16),
            Text(
              'Assessment Criteria:',
              style: GoogleFonts.inter(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 8),
            ...lessonPlan.assessment.criteria.map((criterion) => Padding(
                  padding: EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.check, color: Colors.white54, size: 20),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          criterion,
                          style: GoogleFonts.inter(
                            color: Colors.white70,
                            fontSize: 14,
                          ),
                        ),
                      ),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Widget _buildNextSteps(LessonPlan lessonPlan, BuildContext context) {
    return Card(
      color: Colors.white.withOpacity(0.05),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.arrow_forward,
                    color: Theme.of(context).primaryColor),
                SizedBox(width: 8),
                Text(
                  'Next Steps',
                  style: GoogleFonts.inter(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            SizedBox(height: 16),
            ...lessonPlan.nextSteps.map((step) => Padding(
                  padding: EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.arrow_right, color: Colors.white54, size: 20),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          step,
                          style: GoogleFonts.inter(
                            color: Colors.white70,
                            fontSize: 16,
                          ),
                        ),
                      ),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Color _getKnowledgeLevelColor(String level) {
    switch (level.toLowerCase()) {
      case 'foundational':
        return Colors.blue.withOpacity(0.7);
      case 'intermediate':
        return Colors.green.withOpacity(0.7);
      case 'advanced':
        return Colors.purple.withOpacity(0.7);
      default:
        return Colors.grey.withOpacity(0.7);
    }
  }

  IconData _getResourceIcon(String type) {
    switch (type.toLowerCase()) {
      case 'article':
        return Icons.article;
      case 'video':
        return Icons.video_library;
      case 'interactive':
        return Icons.touch_app;
      case 'worksheet':
        return Icons.assignment;
      case 'book':
        return Icons.book;
      default:
        return Icons.link;
    }
  }
}

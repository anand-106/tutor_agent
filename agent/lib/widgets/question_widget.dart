import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:agent/controllers/chat_controller.dart';
import 'package:google_fonts/google_fonts.dart';
import 'dart:convert';

class QuestionWidget extends StatelessWidget {
  final Map<String, dynamic> question;
  final ChatController chatController = Get.find<ChatController>();

  QuestionWidget({
    Key? key,
    required this.question,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Debug print the question object
    debugPrint('Rendering QuestionWidget with data: ${json.encode(question)}');

    // Extract question properties with safe fallbacks
    final questionType = question['type'] as String? ?? 'general';
    final title = question['title'] as String? ?? 'Question';
    final message = question['message'] as String? ?? '';

    // Check if the options field exists and is properly formatted
    final hasOptions = question.containsKey('options') &&
        question['options'] is List &&
        (question['options'] as List).isNotEmpty;

    // Get options or provide an empty list as fallback
    final options = hasOptions
        ? List<dynamic>.from(question['options'] as List)
        : <dynamic>[];

    if (!hasOptions && questionType == 'multiple_choice') {
      debugPrint(
          'Warning: multiple_choice question type without valid options');
    }

    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Theme.of(context).primaryColor.withOpacity(0.3),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      margin: EdgeInsets.symmetric(vertical: 8),
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Question header
          Row(
            children: [
              Icon(
                _getIconForQuestionType(questionType),
                color: Theme.of(context).primaryColor,
                size: 20,
              ),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  title,
                  style: GoogleFonts.inter(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Theme.of(context).primaryColor,
                  ),
                ),
              ),
            ],
          ),

          // Divider
          Divider(
            color: Colors.white.withOpacity(0.1),
            height: 24,
          ),

          // Question message
          Padding(
            padding: const EdgeInsets.only(bottom: 16.0),
            child: Text(
              message,
              style: GoogleFonts.inter(
                fontSize: 16,
                color: Colors.white.withOpacity(0.9),
              ),
            ),
          ),

          // Options (if present)
          if (hasOptions) ..._buildOptions(context, options, questionType),

          // Fallback if no options are present but they should be
          if (!hasOptions &&
              (questionType == 'multiple_choice' ||
                  questionType == 'topic_selection'))
            Center(
              child: Padding(
                padding: const EdgeInsets.all(8.0),
                child: Text(
                  'No options available for this question.',
                  style: GoogleFonts.inter(
                    fontSize: 14,
                    fontStyle: FontStyle.italic,
                    color: Colors.white.withOpacity(0.7),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  List<Widget> _buildOptions(
      BuildContext context, List<dynamic> options, String questionType) {
    final widgets = <Widget>[];

    debugPrint(
        'Building options for question type: $questionType with ${options.length} options');

    // Build appropriate options based on question type
    if (questionType == 'topic_selection') {
      // Use a responsive grid layout for topics
      final screenWidth = MediaQuery.of(context).size.width;
      final crossAxisCount =
          screenWidth > 600 ? 4 : 3; // More columns on wider screens

      widgets.add(
        GridView.builder(
          shrinkWrap: true,
          physics: NeverScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: crossAxisCount,
            childAspectRatio: 1.0,
            crossAxisSpacing: 8,
            mainAxisSpacing: 8,
          ),
          itemCount: options.length,
          itemBuilder: (context, index) {
            final option = _normalizeOption(options[index], index);
            return _buildCompactTopicCard(context, option, index);
          },
        ),
      );
    } else if (questionType == 'multiple_choice') {
      // Use list tile style options for multiple choice
      for (int i = 0; i < options.length; i++) {
        final option = _normalizeOption(options[i], i);
        widgets.add(_buildOptionListTile(context, option));
        widgets.add(SizedBox(height: 6));
      }
    } else if (questionType == 'confirmation') {
      // Use buttons for yes/no
      widgets.add(
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            for (int i = 0; i < options.length; i++)
              Padding(
                padding: EdgeInsets.symmetric(horizontal: 8),
                child: ElevatedButton(
                  onPressed: () =>
                      _handleOptionSelected(_normalizeOption(options[i], i)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor:
                        _normalizeOption(options[i], i)['id'] == 'yes'
                            ? Colors.green.withOpacity(0.8)
                            : Colors.red.withOpacity(0.8),
                    padding: EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: Text(
                    _normalizeOption(options[i], i)['text'],
                    style: GoogleFonts.inter(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
          ],
        ),
      );
    } else {
      // Default to simple list for other question types
      for (int i = 0; i < options.length; i++) {
        final option = _normalizeOption(options[i], i);
        widgets.add(_buildOptionListTile(context, option));
        widgets.add(SizedBox(height: 6));
      }
    }

    return widgets;
  }

  // Helper method to normalize option format
  Map<String, dynamic> _normalizeOption(dynamic option, int index) {
    if (option is Map<String, dynamic>) {
      // Ensure the option has at least these fields
      return {
        'id': option['id'] ?? '${index + 1}',
        'text': option['text'] ?? 'Option ${index + 1}',
        'description': option['description'] ?? '',
        'is_correct': option['is_correct'] ?? false,
      };
    } else if (option is String) {
      // Convert string to map format
      return {
        'id': '${index + 1}',
        'text': option,
        'description': '',
        'is_correct': false,
      };
    } else {
      // Fallback for unexpected types
      return {
        'id': '${index + 1}',
        'text': 'Option ${index + 1}',
        'description': '',
        'is_correct': false,
      };
    }
  }

  Widget _buildCompactTopicCard(
      BuildContext context, Map<String, dynamic> topic, int index) {
    return Card(
      color: Colors.black.withOpacity(0.3),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(
          color: Theme.of(context).primaryColor.withOpacity(0.3),
        ),
      ),
      elevation: 2,
      margin: EdgeInsets.zero,
      child: InkWell(
        onTap: () => _handleOptionSelected(topic),
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: EdgeInsets.all(6),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Topic number badge
              Container(
                padding: EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: Theme.of(context).primaryColor.withOpacity(0.2),
                  shape: BoxShape.circle,
                ),
                child: Text(
                  '${index + 1}',
                  style: GoogleFonts.inter(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: Theme.of(context).primaryColor,
                  ),
                ),
              ),
              SizedBox(height: 4),
              // Topic title
              Text(
                topic['text'],
                textAlign: TextAlign.center,
                style: GoogleFonts.inter(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              // Only show description if it exists and isn't too long
              if (topic.containsKey('description') &&
                  topic['description'] != null)
                Padding(
                  padding: EdgeInsets.only(top: 2),
                  child: Text(
                    topic['description'],
                    textAlign: TextAlign.center,
                    style: GoogleFonts.inter(
                      fontSize: 10,
                      color: Colors.white.withOpacity(0.6),
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOptionListTile(
      BuildContext context, Map<String, dynamic> option) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: Colors.white.withOpacity(0.1),
        ),
      ),
      child: ListTile(
        dense: true, // Make the list tile more compact
        leading: CircleAvatar(
          radius: 14, // Smaller avatar
          backgroundColor: Theme.of(context).primaryColor.withOpacity(0.2),
          child: Text(
            option['id'],
            style: GoogleFonts.inter(
              color: Theme.of(context).primaryColor,
              fontWeight: FontWeight.bold,
              fontSize: 12, // Smaller text
            ),
          ),
        ),
        title: Text(
          option['text'],
          style: GoogleFonts.inter(
            color: Colors.white.withOpacity(0.9),
            fontSize: 14, // Smaller text
          ),
        ),
        onTap: () => _handleOptionSelected(option),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }

  void _handleOptionSelected(Map<String, dynamic> option) {
    // Get option ID and text
    final optionId = option['id'];
    final optionText = option['text'];

    debugPrint('Selected option: ID=$optionId, Text=$optionText');

    // For topic selection, send the option ID
    final questionType = question['type'] as String? ?? 'general';
    if (questionType == 'topic_selection') {
      debugPrint('Topic selection detected, sending ID: $optionId');
      chatController.sendMessage(optionId);
    } else {
      // Get relevant info from the question to include in response
      final questionMessage = question['message'] as String? ?? '';

      // For multiple choice and other types, construct a formatted response
      // This helps the backend identify it as an answer to a question
      String responseText = "!answer:$optionId:$optionText";

      debugPrint('Sending formatted answer response: $responseText');
      chatController.sendMessage(responseText, isQuestionResponse: true);
    }
  }

  IconData _getIconForQuestionType(String questionType) {
    switch (questionType) {
      case 'topic_selection':
        return Icons.topic;
      case 'multiple_choice':
        return Icons.quiz;
      case 'confirmation':
        return Icons.check_circle;
      default:
        return Icons.question_answer;
    }
  }
}

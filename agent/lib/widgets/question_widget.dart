import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:agent/controllers/chat_controller.dart';
import 'package:google_fonts/google_fonts.dart';

class QuestionWidget extends StatelessWidget {
  final Map<String, dynamic> question;
  final ChatController chatController = Get.find<ChatController>();

  QuestionWidget({
    Key? key,
    required this.question,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final questionType = question['type'] as String? ?? 'general';
    final title = question['title'] as String? ?? 'Question';
    final message = question['message'] as String? ?? '';
    final hasOptions = question['has_options'] as bool? ?? false;
    final options = question['options'] as List<dynamic>? ?? [];

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
      padding: EdgeInsets.all(12),
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
              Text(
                title,
                style: GoogleFonts.inter(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).primaryColor,
                ),
              ),
            ],
          ),

          // Divider
          Divider(
            color: Colors.white.withOpacity(0.1),
            height: 16,
          ),

          // Question message
          Text(
            message,
            style: GoogleFonts.inter(
              fontSize: 14,
              color: Colors.white.withOpacity(0.9),
            ),
          ),

          SizedBox(height: 12),

          // Options (if present)
          if (hasOptions && options.isNotEmpty)
            ..._buildOptions(context, options, questionType),
        ],
      ),
    );
  }

  List<Widget> _buildOptions(
      BuildContext context, List<dynamic> options, String questionType) {
    final widgets = <Widget>[];

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
            final option = options[index];
            return _buildCompactTopicCard(context, option, index);
          },
        ),
      );
    } else if (questionType == 'multiple_choice') {
      // Use list tile style options for multiple choice
      for (final option in options) {
        widgets.add(_buildOptionListTile(context, option));
        widgets.add(SizedBox(height: 6));
      }
    } else if (questionType == 'confirmation') {
      // Use buttons for yes/no
      widgets.add(
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            for (final option in options)
              Padding(
                padding: EdgeInsets.symmetric(horizontal: 8),
                child: ElevatedButton(
                  onPressed: () => _handleOptionSelected(option),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: option['id'] == 'yes'
                        ? Colors.green.withOpacity(0.8)
                        : Colors.red.withOpacity(0.8),
                    padding: EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: Text(
                    option['text'],
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
      for (final option in options) {
        widgets.add(_buildOptionListTile(context, option));
        widgets.add(SizedBox(height: 6));
      }
    }

    return widgets;
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

  Widget _buildTopicCard(BuildContext context, Map<String, dynamic> topic) {
    return Card(
      color: Colors.black.withOpacity(0.3),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: Theme.of(context).primaryColor.withOpacity(0.3),
        ),
      ),
      elevation: 4,
      child: InkWell(
        onTap: () => _handleOptionSelected(topic),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: EdgeInsets.all(12),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                topic['text'],
                textAlign: TextAlign.center,
                style: GoogleFonts.inter(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              if (topic.containsKey('description') &&
                  topic['description'] != null)
                Padding(
                  padding: EdgeInsets.only(top: 4),
                  child: Text(
                    topic['description'],
                    textAlign: TextAlign.center,
                    style: GoogleFonts.inter(
                      fontSize: 12,
                      color: Colors.white.withOpacity(0.7),
                    ),
                    maxLines: 2,
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
    // Send the selected option to the chat controller
    final optionText = option['text'];
    final optionId = option['id'];

    // Form the response in a way the backend will understand
    chatController.sendMessage(optionId);
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

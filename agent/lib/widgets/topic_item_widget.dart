import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:agent/controllers/chat_controller.dart';
import 'package:google_fonts/google_fonts.dart';

class TopicItemWidget extends StatelessWidget {
  final String title;
  final List<dynamic>? subtopics;
  final ChatController chatController;

  const TopicItemWidget({
    required this.title,
    this.subtopics,
    required this.chatController,
    Key? key,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: EdgeInsets.symmetric(vertical: 4),
          child: Container(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                chatController.sendMessage("Teach me about: $title");
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white.withOpacity(0.05),
                foregroundColor: Colors.white,
                elevation: 0,
                padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(
                    color: Theme.of(context).primaryColor.withOpacity(0.3),
                  ),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      title,
                      style: GoogleFonts.inter(
                        fontSize: 15,
                        fontWeight: FontWeight.w500,
                        color: Colors.white.withOpacity(0.9),
                      ),
                    ),
                  ),
                  Icon(
                    Icons.arrow_forward_rounded,
                    size: 20,
                    color: Theme.of(context).primaryColor,
                  ),
                ],
              ),
            ),
          ),
        ),
        if (subtopics != null)
          Padding(
            padding: EdgeInsets.only(left: 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: subtopics!.map((subtopic) {
                if (subtopic is Map<String, dynamic>) {
                  return TopicItemWidget(
                    title: subtopic['title'] ?? '',
                    subtopics: subtopic['subtopics'],
                    chatController: chatController,
                  );
                }
                return SizedBox.shrink();
              }).toList(),
            ),
          ),
      ],
    );
  }
}

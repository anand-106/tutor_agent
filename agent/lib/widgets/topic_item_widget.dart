import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:agent/controllers/chat_controller.dart';

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
          child: ElevatedButton(
            onPressed: () {
              chatController.sendMessage("Teach me about: $title");
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: Theme.of(context).primaryColor,
              elevation: 1,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
                side: BorderSide(
                    color: Theme.of(context).primaryColor.withOpacity(0.2)),
              ),
            ),
            child: Text(title),
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

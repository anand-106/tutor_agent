import 'package:flutter/material.dart';
import 'package:agent/models/chat_message.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

class ChatMessageWidget extends StatelessWidget {
  final ChatMessage message;

  const ChatMessageWidget({required this.message});

  @override
  Widget build(BuildContext context) {
    // Debug print
    print('Message text: ${message.text}');

    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints:
            BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        margin: EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        padding: EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: message.isUser ? Colors.blue[100] : Colors.grey[200],
          borderRadius: BorderRadius.circular(12),
        ),
        child: message.isUser
            ? Text(message.text)
            : SingleChildScrollView(
                child: MarkdownBody(
                  data: message.text,
                  selectable: true,
                  shrinkWrap: true,
                  softLineBreak: true,
                  styleSheet: MarkdownStyleSheet(
                    p: TextStyle(fontSize: 16),
                    code: TextStyle(
                      backgroundColor: Colors.grey[300],
                      fontFamily: 'monospace',
                    ),
                  ),
                ),
              ),
      ),
    );
  }
}

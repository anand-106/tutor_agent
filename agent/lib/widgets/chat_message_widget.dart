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
import 'package:agent/widgets/flashcard_widget.dart';
import 'package:agent/widgets/question_widget.dart';

class ChatMessageWidget extends StatelessWidget {
  final ChatMessage message;
  final ChatController chatController = Get.find<ChatController>();
  final DocumentController documentController = Get.find<DocumentController>();

  ChatMessageWidget({
    Key? key,
    required this.message,
  }) : super(key: key);

  bool isTopicsMessage() {
    return message.response
        .startsWith("Here are the topics extracted from your document:");
  }

  @override
  Widget build(BuildContext context) {
    // Check if the message is from a dynamic flow teaching mode
    if (message.teachingMode == 'dynamic_flow') {
      return Align(
        alignment: Alignment.centerLeft,
        child: Container(
          constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.95,
            minWidth: MediaQuery.of(context).size.width * 0.85,
          ),
          margin: EdgeInsets.symmetric(vertical: 8, horizontal: 8),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(20),
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
              child: Container(
                padding: EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.05),
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
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Visual indicator this is a learning flow
                    Row(
                      children: [
                        Icon(
                          Icons.school,
                          color: Theme.of(context).primaryColor,
                          size: 18,
                        ),
                        SizedBox(width: 8),
                        Text(
                          'Interactive Learning Flow',
                          style: GoogleFonts.inter(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: Theme.of(context).primaryColor,
                          ),
                        ),
                      ],
                    ),
                    Divider(
                      color: Colors.white.withOpacity(0.1),
                      height: 16,
                    ),

                    // Flow content as markdown
                    MarkdownBody(
                      data: message.response,
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
                      ),
                    ),

                    // Show diagram if present
                    if (message.hasDiagram && message.mermaidCode != null) ...[
                      SizedBox(height: 20),
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

                    // Show quiz if present
                    if (message.hasQuestion && message.question != null) ...[
                      SizedBox(height: 20),
                      Container(
                        margin: EdgeInsets.only(top: 16),
                        child: QuestionWidget(question: message.question!),
                      ),
                    ],

                    // Show flashcards if present
                    if (message.hasFlashcards &&
                        message.flashcards != null) ...[
                      SizedBox(height: 20),
                      Container(
                        margin: EdgeInsets.only(top: 16),
                        child: FlashcardWidget(
                          flashcardsData: message.flashcards!,
                          onPinCard: (card) {
                            if (card['is_pinned']) {
                              chatController.pinCard(card);
                            } else {
                              chatController.unpinCard(card);
                            }
                          },
                          onPinAll: (cards) {
                            chatController.pinAllCards(cards
                                .map((c) => Map<String, dynamic>.from(c))
                                .toList());
                          },
                        ),
                      ),
                    ],

                    // Navigation buttons
                    SizedBox(height: 20),
                    Container(
                      padding: EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: Colors.white.withOpacity(0.05),
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Navigation',
                            style: GoogleFonts.inter(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: Colors.white.withOpacity(0.7),
                            ),
                          ),
                          SizedBox(height: 8),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                            children: [
                              _buildFlowButton(
                                  context, 'Previous', Icons.arrow_back, () {
                                chatController.sendMessage('previous');
                              }),
                              _buildFlowButton(
                                  context, 'Next', Icons.arrow_forward, () {
                                chatController.sendMessage('next');
                              }),
                              _buildFlowButton(
                                  context, 'List Topics', Icons.list, () {
                                chatController.sendMessage('list topics');
                              }),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
    }

    // Check if the message contains an interactive question
    if (message.hasQuestion && message.question != null) {
      debugPrint(
          'Rendering interactive question: ${json.encode(message.question)}');
      return Align(
        alignment: Alignment.centerLeft,
        child: Container(
          constraints: BoxConstraints(
            // Increase max width for better display of grid items
            maxWidth: MediaQuery.of(context).size.width * 0.95,
            // Add a minimum width to ensure small screens still have enough space
            minWidth: MediaQuery.of(context).size.width * 0.85,
          ),
          margin: EdgeInsets.symmetric(
              vertical: 8, horizontal: 8), // Reduced horizontal margin
          child: QuestionWidget(question: message.question!),
        ),
      );
    }

    // Check if the response is a flashcard message
    if (message.response is String) {
      try {
        // First try to parse the entire response as JSON
        final Map<String, dynamic> jsonData = json.decode(message.response);
        Map<String, dynamic> flashcardsData;

        // Check if the flashcards data is nested inside another object
        if (jsonData.containsKey('flashcards') &&
            jsonData['flashcards'] is Map<String, dynamic>) {
          // Extract the nested flashcards data
          flashcardsData = jsonData['flashcards'] as Map<String, dynamic>;
          debugPrint('Extracted nested flashcards data at beginning of build');
        } else {
          // Use the data as is
          flashcardsData = jsonData;
        }

        if (flashcardsData.containsKey('flashcards') &&
            (flashcardsData.containsKey('topic') ||
                flashcardsData.containsKey('description'))) {
          debugPrint('Creating flashcard widget from direct JSON');

          // Ensure each flashcard has required fields
          List<Map<String, dynamic>> flashcards = [];
          if (flashcardsData['flashcards'] is List &&
              (flashcardsData['flashcards'] as List).isNotEmpty) {
            flashcards =
                List<Map<String, dynamic>>.from(flashcardsData['flashcards']);
            for (var i = 0; i < flashcards.length; i++) {
              if (!flashcards[i].containsKey('id')) {
                flashcards[i]['id'] = 'card_${i + 1}';
              }
              if (!flashcards[i].containsKey('is_pinned')) {
                flashcards[i]['is_pinned'] = false;
              }
            }
          } else {
            // Create a default flashcard if the list is empty
            flashcards = [
              {
                "id": "default_card",
                "front": {
                  "title": "No flashcards available",
                  "points": ["Try asking for flashcards on a specific topic"]
                },
                "back": {
                  "explanation":
                      "The system couldn't generate flashcards based on the current context.",
                  "points": [
                    "Try uploading a document with more content",
                    "Specify a topic more clearly"
                  ]
                },
                "is_pinned": false
              }
            ];
          }

          flashcardsData['flashcards'] = flashcards;
          // Ensure topic and description exist (they'll be handled with defaults in the FlashcardWidget)
          if (!flashcardsData.containsKey('topic')) {
            flashcardsData['topic'] = null;
          }
          if (!flashcardsData.containsKey('description')) {
            flashcardsData['description'] = null;
          }

          debugPrint('Processed flashcards: ${json.encode(flashcards)}');
          return FlashcardWidget(
            flashcardsData: flashcardsData,
            onPinCard: (card) {
              debugPrint('Pin card called with: ${json.encode(card)}');
              if (card['is_pinned']) {
                chatController.pinCard(card);
              } else {
                chatController.unpinCard(card);
              }
            },
            onPinAll: (cards) {
              debugPrint('Pin all cards called with ${cards.length} cards');
              chatController.pinAllCards(
                  cards.map((c) => Map<String, dynamic>.from(c)).toList());
            },
          );
        }
      } catch (e) {
        debugPrint('First JSON parse attempt failed: $e');
        // If direct parsing fails, try to extract JSON from code blocks
        if (message.response.contains('```json')) {
          try {
            RegExp regExp = RegExp(r'```json\s*([\s\S]*?)\s*```');
            Match? match = regExp.firstMatch(message.response);

            if (match != null) {
              String jsonText = match.group(1)?.trim() ?? '';
              jsonText = jsonText
                  .replaceAll(RegExp(r',(\s*[}\]])', multiLine: true), r'$1')
                  .replaceAll(RegExp(r'[\n\r]'), '')
                  .trim();

              final data = json.decode(jsonText);
              if (data is Map<String, dynamic> &&
                  data.containsKey('flashcards') &&
                  data.containsKey('topic')) {
                debugPrint('Creating flashcard widget from code block');

                // Ensure each flashcard has required fields
                final List<Map<String, dynamic>> flashcards =
                    List<Map<String, dynamic>>.from(data['flashcards']);
                for (var i = 0; i < flashcards.length; i++) {
                  if (!flashcards[i].containsKey('id')) {
                    flashcards[i]['id'] = 'card_${i + 1}';
                  }
                  if (!flashcards[i].containsKey('is_pinned')) {
                    flashcards[i]['is_pinned'] = false;
                  }
                }
                data['flashcards'] = flashcards;

                debugPrint(
                    'Processed flashcards from code block: ${json.encode(flashcards)}');
                return FlashcardWidget(
                  flashcardsData: data,
                  onPinCard: (card) {
                    debugPrint('Pin card called with: ${json.encode(card)}');
                    if (card['is_pinned']) {
                      chatController.pinCard(card);
                    } else {
                      chatController.unpinCard(card);
                    }
                  },
                  onPinAll: (cards) {
                    debugPrint(
                        'Pin all cards called with ${cards.length} cards');
                    chatController.pinAllCards(cards
                        .map((c) => Map<String, dynamic>.from(c))
                        .toList());
                  },
                );
              }
            }
          } catch (e) {
            debugPrint('Code block JSON parse attempt failed: $e');
          }
        }
      }
    }

    // Check if this message has a diagram
    if (message.hasDiagram && message.mermaidCode != null) {
      debugPrint('Rendering diagram directly from message properties');
      return Align(
        alignment: Alignment.centerLeft,
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
                  color: Colors.white.withOpacity(0.05),
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
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    MarkdownBody(data: message.response),
                    SizedBox(height: 16),
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
                ),
              ),
            ),
          ),
        ),
      );
    }

    // Check if this message contains quiz data
    if (message.response.contains('"questions"') &&
        message.response.contains('"topic"')) {
      debugPrint('Rendering quiz directly from message response');
      try {
        // Try to parse the response as JSON
        final Map<String, dynamic> quizData = json.decode(message.response);
        if (quizData.containsKey('questions') &&
            quizData.containsKey('topic')) {
          return Align(
            alignment: Alignment.centerLeft,
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
                      color: Colors.white.withOpacity(0.05),
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
                    child: QuizWidget(quizData: quizData),
                  ),
                ),
              ),
            ),
          );
        }
      } catch (e) {
        debugPrint('Error parsing quiz data: $e');
        // If direct parsing fails, try to extract JSON from code blocks
        if (message.response.contains('```json')) {
          try {
            RegExp regExp = RegExp(r'```json\s*([\s\S]*?)\s*```');
            Match? match = regExp.firstMatch(message.response);

            if (match != null) {
              String jsonText = match.group(1)?.trim() ?? '';
              jsonText = jsonText
                  .replaceAll(RegExp(r',(\s*[}\]])', multiLine: true), r'$1')
                  .replaceAll(RegExp(r'[\n\r]'), '')
                  .trim();

              final data = json.decode(jsonText);
              if (data is Map<String, dynamic> &&
                  data.containsKey('questions') &&
                  data.containsKey('topic')) {
                return Align(
                  alignment: Alignment.centerLeft,
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
                            color: Colors.white.withOpacity(0.05),
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
                          child: QuizWidget(quizData: data),
                        ),
                      ),
                    ),
                  ),
                );
              }
            }
          } catch (e) {
            debugPrint('Error parsing quiz data from code block: $e');
          }
        }
      }
    }

    // Check if this message contains flashcard data
    if (message.response.contains('"flashcards"') &&
        (message.response.contains('"topic"') ||
            message.response.contains('"response"') ||
            message.response.contains('"description"'))) {
      debugPrint('Rendering flashcards directly from message response');
      try {
        // Try to parse the response as JSON
        final Map<String, dynamic> jsonData = json.decode(message.response);
        Map<String, dynamic> flashcardsData;

        // Check if the flashcards data is nested inside another object
        if (jsonData.containsKey('flashcards') &&
            jsonData['flashcards'] is Map<String, dynamic>) {
          // Extract the nested flashcards data
          flashcardsData = jsonData['flashcards'] as Map<String, dynamic>;
          debugPrint('Extracted nested flashcards data');
        } else {
          // Use the data as is
          flashcardsData = jsonData;
        }

        if (flashcardsData.containsKey('flashcards') &&
            (flashcardsData.containsKey('topic') ||
                flashcardsData.containsKey('description'))) {
          // Ensure each flashcard has required fields
          List<Map<String, dynamic>> flashcards = [];
          if (flashcardsData['flashcards'] is List &&
              (flashcardsData['flashcards'] as List).isNotEmpty) {
            flashcards =
                List<Map<String, dynamic>>.from(flashcardsData['flashcards']);
            for (var i = 0; i < flashcards.length; i++) {
              if (!flashcards[i].containsKey('id')) {
                flashcards[i]['id'] = 'card_${i + 1}';
              }
              if (!flashcards[i].containsKey('is_pinned')) {
                flashcards[i]['is_pinned'] = false;
              }
            }
          } else {
            // Create a default flashcard if the list is empty
            flashcards = [
              {
                "id": "default_card",
                "front": {
                  "title": "No flashcards available",
                  "points": ["Try asking for flashcards on a specific topic"]
                },
                "back": {
                  "explanation":
                      "The system couldn't generate flashcards based on the current context.",
                  "points": [
                    "Try uploading a document with more content",
                    "Specify a topic more clearly"
                  ]
                },
                "is_pinned": false
              }
            ];
          }
          flashcardsData['flashcards'] = flashcards;

          // Ensure topic and description exist
          if (!flashcardsData.containsKey('topic')) {
            flashcardsData['topic'] = null;
          }
          if (!flashcardsData.containsKey('description')) {
            flashcardsData['description'] = null;
          }

          debugPrint('Processed flashcards: ${json.encode(flashcards)}');

          return Align(
            alignment: Alignment.centerLeft,
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
                      color: Colors.white.withOpacity(0.05),
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
                    child: FlashcardWidget(
                      flashcardsData: flashcardsData,
                      onPinCard: (card) {
                        debugPrint(
                            'Pin card called with: ${json.encode(card)}');
                        if (card['is_pinned']) {
                          chatController.pinCard(card);
                        } else {
                          chatController.unpinCard(card);
                        }
                      },
                      onPinAll: (cards) {
                        debugPrint(
                            'Pin all cards called with ${cards.length} cards');
                        chatController.pinAllCards(cards
                            .map((c) => Map<String, dynamic>.from(c))
                            .toList());
                      },
                    ),
                  ),
                ),
              ),
            ),
          );
        }
      } catch (e) {
        debugPrint('Error parsing flashcard data: $e');
        // If direct parsing fails, try to extract JSON from code blocks
        if (message.response.contains('```json')) {
          try {
            RegExp regExp = RegExp(r'```json\s*([\s\S]*?)\s*```');
            Match? match = regExp.firstMatch(message.response);

            if (match != null) {
              String jsonText = match.group(1)?.trim() ?? '';
              jsonText = jsonText
                  .replaceAll(RegExp(r',(\s*[}\]])', multiLine: true), r'$1')
                  .replaceAll(RegExp(r'[\n\r]'), '')
                  .trim();

              final data = json.decode(jsonText);
              Map<String, dynamic> flashcardsData;

              // Check if the flashcards data is nested inside another object
              if (data is Map<String, dynamic> &&
                  data.containsKey('flashcards') &&
                  data['flashcards'] is Map<String, dynamic>) {
                // Extract the nested flashcards data
                flashcardsData = data['flashcards'] as Map<String, dynamic>;
                debugPrint('Extracted nested flashcards data from code block');
              } else {
                // Use the data as is
                flashcardsData = data;
              }

              if (flashcardsData is Map<String, dynamic> &&
                  flashcardsData.containsKey('flashcards') &&
                  (flashcardsData.containsKey('topic') ||
                      flashcardsData.containsKey('description'))) {
                // Ensure each flashcard has required fields
                List<Map<String, dynamic>> flashcards = [];
                if (flashcardsData['flashcards'] is List &&
                    (flashcardsData['flashcards'] as List).isNotEmpty) {
                  flashcards = List<Map<String, dynamic>>.from(
                      flashcardsData['flashcards']);
                  for (var i = 0; i < flashcards.length; i++) {
                    if (!flashcards[i].containsKey('id')) {
                      flashcards[i]['id'] = 'card_${i + 1}';
                    }
                    if (!flashcards[i].containsKey('is_pinned')) {
                      flashcards[i]['is_pinned'] = false;
                    }
                  }
                } else {
                  // Create a default flashcard if the list is empty
                  flashcards = [
                    {
                      "id": "default_card",
                      "front": {
                        "title": "No flashcards available",
                        "points": [
                          "Try asking for flashcards on a specific topic"
                        ]
                      },
                      "back": {
                        "explanation":
                            "The system couldn't generate flashcards based on the current context.",
                        "points": [
                          "Try uploading a document with more content",
                          "Specify a topic more clearly"
                        ]
                      },
                      "is_pinned": false
                    }
                  ];
                }
                flashcardsData['flashcards'] = flashcards;

                // Ensure topic and description exist
                if (!flashcardsData.containsKey('topic')) {
                  flashcardsData['topic'] = null;
                }
                if (!flashcardsData.containsKey('description')) {
                  flashcardsData['description'] = null;
                }

                debugPrint('Processed flashcards: ${json.encode(flashcards)}');

                return Align(
                  alignment: Alignment.centerLeft,
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
                            color: Colors.white.withOpacity(0.05),
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
                          child: FlashcardWidget(
                            flashcardsData: flashcardsData,
                            onPinCard: (card) {
                              debugPrint(
                                  'Pin card called with: ${json.encode(card)}');
                              if (card['is_pinned']) {
                                chatController.pinCard(card);
                              } else {
                                chatController.unpinCard(card);
                              }
                            },
                            onPinAll: (cards) {
                              debugPrint(
                                  'Pin all cards called with ${cards.length} cards');
                              chatController.pinAllCards(cards
                                  .map((c) => Map<String, dynamic>.from(c))
                                  .toList());
                            },
                          ),
                        ),
                      ),
                    ),
                  ),
                );
              }
            }
          } catch (e) {
            debugPrint('Error parsing flashcard data from code block: $e');
          }
        }
      }
    }

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
          print('Found JSON: $jsonText'); // Debug print

          try {
            // Clean up the JSON text
            jsonText = jsonText
                .replaceAll(RegExp(r',(\s*[}\]])', multiLine: true), r'$1')
                .replaceAll(RegExp(r'[\n\r]'), '')
                .trim();

            final data = json.decode(jsonText);
            print('Parsed data: $data'); // Debug print

            // Check if this is a quiz response
            if (data is Map<String, dynamic> &&
                data.containsKey('questions') &&
                data.containsKey('topic')) {
              print('Creating quiz widget with data: $data'); // Debug print
              return QuizWidget(quizData: data);
            }
            // Check if this is a diagram response
            else if (data is Map<String, dynamic> &&
                data.containsKey('explanation') &&
                data.containsKey('mermaid_code')) {
              print('Creating diagram widget with data: $data'); // Debug print
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (data['explanation'].toString().isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 16.0),
                      child: MarkdownBody(data: data['explanation'].toString()),
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
                      diagramCode: data['mermaid_code'].toString(),
                      width: MediaQuery.of(context).size.width * 0.8,
                      height: 400,
                    ),
                  ),
                ],
              );
            }
            // Check if this is an explanation response
            else if (data is Map<String, dynamic> &&
                data.containsKey('title') &&
                data.containsKey('summary')) {
              print(
                  'Creating explanation widget with data: $data'); // Debug print
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
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      data['title'].toString(),
                      style: GoogleFonts.inter(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Theme.of(context).primaryColor,
                      ),
                    ),
                    SizedBox(height: 16),
                    Text(
                      data['summary'].toString(),
                      style: GoogleFonts.inter(
                        fontSize: 16,
                        color: Colors.white.withOpacity(0.9),
                      ),
                    ),
                    if (data['key_points'] is List &&
                        data['key_points'].isNotEmpty) ...[
                      SizedBox(height: 16),
                      Text(
                        'Key Points:',
                        style: GoogleFonts.inter(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                          color: Colors.white.withOpacity(0.9),
                        ),
                      ),
                      SizedBox(height: 8),
                      ...List.generate(
                        data['key_points'].length,
                        (index) => Padding(
                          padding: const EdgeInsets.only(bottom: 8.0),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '• ',
                                style: GoogleFonts.inter(
                                  fontSize: 16,
                                  color: Theme.of(context).primaryColor,
                                ),
                              ),
                              Expanded(
                                child: Text(
                                  data['key_points'][index].toString(),
                                  style: GoogleFonts.inter(
                                    fontSize: 16,
                                    color: Colors.white.withOpacity(0.9),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                    if (data['detailed_explanation']?.toString().isNotEmpty ??
                        false) ...[
                      SizedBox(height: 16),
                      Text(
                        'Detailed Explanation:',
                        style: GoogleFonts.inter(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                          color: Colors.white.withOpacity(0.9),
                        ),
                      ),
                      SizedBox(height: 8),
                      Text(
                        data['detailed_explanation'].toString(),
                        style: GoogleFonts.inter(
                          fontSize: 16,
                          color: Colors.white.withOpacity(0.9),
                        ),
                      ),
                    ],
                    if (data['examples'] is List &&
                        data['examples'].isNotEmpty) ...[
                      SizedBox(height: 16),
                      Text(
                        'Examples:',
                        style: GoogleFonts.inter(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                          color: Colors.white.withOpacity(0.9),
                        ),
                      ),
                      SizedBox(height: 8),
                      ...List.generate(
                        data['examples'].length,
                        (index) => Padding(
                          padding: const EdgeInsets.only(bottom: 8.0),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${index + 1}. ',
                                style: GoogleFonts.inter(
                                  fontSize: 16,
                                  color: Theme.of(context).primaryColor,
                                ),
                              ),
                              Expanded(
                                child: Text(
                                  data['examples'][index].toString(),
                                  style: GoogleFonts.inter(
                                    fontSize: 16,
                                    color: Colors.white.withOpacity(0.9),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                    if (data['additional_notes']?.toString().isNotEmpty ??
                        false) ...[
                      SizedBox(height: 16),
                      Text(
                        'Additional Notes:',
                        style: GoogleFonts.inter(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                          color: Colors.white.withOpacity(0.9),
                        ),
                      ),
                      SizedBox(height: 8),
                      Text(
                        data['additional_notes'].toString(),
                        style: GoogleFonts.inter(
                          fontSize: 16,
                          color: Colors.white.withOpacity(0.9),
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ],
                ),
              );
            }
            // Check if this is a flashcard response
            else if (data is Map<String, dynamic> &&
                data.containsKey('flashcards') &&
                data.containsKey('topic')) {
              print(
                  'Creating flashcard widget with data: $data'); // Debug print
              return FlashcardWidget(
                flashcardsData: data,
                onPinCard: (card) {
                  debugPrint('Pin card called with: ${json.encode(card)}');
                  if (card['is_pinned']) {
                    chatController.pinCard(card);
                  } else {
                    chatController.unpinCard(card);
                  }
                },
                onPinAll: (cards) {
                  debugPrint('Pin all cards called with ${cards.length} cards');
                  chatController.pinAllCards(
                      cards.map((c) => Map<String, dynamic>.from(c)).toList());
                },
              );
            } else {
              print('Invalid data format: $data'); // Debug print
            }
          } catch (e) {
            print('Error parsing JSON: $e'); // Debug print
          }
        } else {
          print('No JSON content found in markdown blocks'); // Debug print
        }
      } catch (e) {
        print('Error processing response: $e'); // Debug print
      }
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
          SizedBox(height: 20),
          Center(
            child: ElevatedButton.icon(
              icon: Icon(Icons.play_arrow),
              label: Text(
                'Start Studying All Topics',
                style: GoogleFonts.inter(
                  fontWeight: FontWeight.bold,
                ),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: Theme.of(context).primaryColor,
                foregroundColor: Colors.white,
                padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                elevation: 3,
              ),
              onPressed: () {
                // Get the document controller and start the study flow
                final documentController = Get.find<DocumentController>();
                documentController.startStudyingFlow();
              },
            ),
          ),
        ],
      ),
    );
  }

  // Method to build a flow navigation button
  Widget _buildFlowButton(BuildContext context, String label, IconData icon,
      VoidCallback onPressed) {
    return ElevatedButton.icon(
      icon: Icon(icon, size: 16),
      label: Text(label),
      style: ElevatedButton.styleFrom(
        backgroundColor: Theme.of(context).primaryColor.withOpacity(0.2),
        foregroundColor: Colors.white,
        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
        ),
      ),
      onPressed: onPressed,
    );
  }
}

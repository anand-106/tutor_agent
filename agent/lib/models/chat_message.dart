class ChatMessage {
  final String response;
  final bool isUser;
  final bool hasDiagram;
  final String? mermaidCode;
  final String? diagramType;
  final bool hasQuestion;
  final Map<String, dynamic>? question;
  final bool hasFlashcards;
  final Map<String, dynamic>? flashcards;
  final String? teachingMode;

  ChatMessage({
    required this.response,
    required this.isUser,
    this.hasDiagram = false,
    this.mermaidCode,
    this.diagramType,
    this.hasQuestion = false,
    this.question,
    this.hasFlashcards = false,
    this.flashcards,
    this.teachingMode,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      response: json['response'] as String,
      isUser: json['isUser'] as bool? ?? false,
      hasDiagram: json['has_diagram'] as bool? ?? false,
      mermaidCode: json['mermaid_code'] as String?,
      diagramType: json['diagram_type'] as String?,
      hasQuestion: json['has_question'] as bool? ?? false,
      question: json['question'] != null
          ? Map<String, dynamic>.from(json['question'] as Map)
          : null,
      hasFlashcards: json['has_flashcards'] as bool? ?? false,
      flashcards: json['flashcards'] != null
          ? Map<String, dynamic>.from(json['flashcards'] as Map)
          : null,
      teachingMode: json['teaching_mode'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'response': response,
      'isUser': isUser,
      'has_diagram': hasDiagram,
      'mermaid_code': mermaidCode,
      'diagram_type': diagramType,
      'has_question': hasQuestion,
      'question': question,
      'has_flashcards': hasFlashcards,
      'flashcards': flashcards,
      'teaching_mode': teachingMode,
    };
  }
}

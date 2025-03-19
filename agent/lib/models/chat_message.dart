class ChatMessage {
  final String response;
  final bool isUser;
  final bool hasDiagram;
  final String? mermaidCode;
  final String? diagramType;
  final bool hasQuestion;
  final Map<String, dynamic>? question;

  ChatMessage({
    required this.response,
    required this.isUser,
    this.hasDiagram = false,
    this.mermaidCode,
    this.diagramType,
    this.hasQuestion = false,
    this.question,
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
    };
  }
}

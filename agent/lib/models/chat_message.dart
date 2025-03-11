class ChatMessage {
  final String response;
  final bool isUser;
  final bool hasDiagram;
  final String? mermaidCode;
  final String? diagramType;

  ChatMessage({
    required this.response,
    required this.isUser,
    this.hasDiagram = false,
    this.mermaidCode,
    this.diagramType,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      response: json['response'] as String,
      isUser: json['isUser'] as bool? ?? false,
      hasDiagram: json['has_diagram'] as bool? ?? false,
      mermaidCode: json['mermaid_code'] as String?,
      diagramType: json['diagram_type'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'response': response,
      'isUser': isUser,
      'has_diagram': hasDiagram,
      'mermaid_code': mermaidCode,
      'diagram_type': diagramType,
    };
  }
}

class Document {
  final String name;
  final String path;
  final DateTime uploadTime;

  Document({
    required this.name,
    required this.path,
    DateTime? uploadTime,
  }) : uploadTime = uploadTime ?? DateTime.now();
}

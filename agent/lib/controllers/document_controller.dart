import 'package:get/get.dart';
import 'package:agent/models/document.dart';
import 'package:agent/services/api_service.dart';
import 'package:file_picker/file_picker.dart';
import 'package:agent/controllers/chat_controller.dart';

class DocumentController extends GetxController {
  final ApiService _apiService = Get.find<ApiService>();
  final ChatController _chatController = Get.find<ChatController>();
  final RxList<Document> documents = <Document>[].obs;
  final RxBool isUploading = false.obs;

  Future<void> uploadDocument() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'docx', 'txt'],
        withData: true,
      );

      if (result != null && result.files.isNotEmpty) {
        isUploading.value = true;

        final file = result.files.first;
        await _apiService.uploadDocument(file);

        documents.add(Document(
          name: file.name,
          path: file.name,
        ));

        // Fetch and display topics
        final topics = await _apiService.getTopics();
        _displayTopics(topics);

        Get.snackbar('Success', 'Document uploaded successfully');
      }
    } catch (e) {
      Get.snackbar('Error', 'Failed to upload document: $e');
    } finally {
      isUploading.value = false;
    }
  }

  void _displayTopics(Map<String, dynamic> topics) {
    final topicsMarkdown = _convertTopicsToMarkdown(topics);
    _chatController.addSystemMessage(
        "Here are the topics extracted from your document:\n\n$topicsMarkdown");
  }

  String _convertTopicsToMarkdown(Map<String, dynamic> topics) {
    StringBuffer markdown = StringBuffer();

    topics.forEach((filename, content) {
      if (content is Map<String, dynamic>) {
        markdown.writeln('# ${content['title']}\n');

        if (content['subtopics'] != null) {
          _addSubtopics(markdown, content['subtopics'] as List, 0);
        }
      }
    });

    return markdown.toString();
  }

  void _addSubtopics(StringBuffer markdown, List subtopics, int level) {
    for (var subtopic in subtopics) {
      if (subtopic is Map<String, dynamic>) {
        String indent = '  ' * level;
        String bullet = level == 0 ? '##' : '•';

        markdown.writeln('$indent$bullet ${subtopic['title']}');
        if (subtopic['content'] != null &&
            subtopic['content'].toString().isNotEmpty) {
          markdown.writeln('$indent  ${subtopic['content']}\n');
        }

        if (subtopic['subtopics'] != null &&
            (subtopic['subtopics'] as List).isNotEmpty) {
          _addSubtopics(markdown, subtopic['subtopics'] as List, level + 1);
        }
      }
    }
  }
}

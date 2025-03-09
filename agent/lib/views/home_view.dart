import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'dart:ui';
import 'package:agent/controllers/chat_controller.dart';
import 'package:agent/controllers/document_controller.dart';
import 'package:agent/widgets/chat_widget.dart';
import 'package:agent/widgets/document_upload_widget.dart';
import 'package:google_fonts/google_fonts.dart';

class HomeView extends GetView<ChatController> {
  final DocumentController documentController = Get.put(DocumentController());
  final RxBool isLeftPanelExpanded = true.obs;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF121212),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        flexibleSpace: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                border: Border(
                  bottom: BorderSide(
                    color: Colors.white.withOpacity(0.1),
                  ),
                ),
              ),
            ),
          ),
        ),
        leading: IconButton(
          icon: Icon(Icons.menu, color: Colors.white70),
          onPressed: () => isLeftPanelExpanded.toggle(),
        ),
        title: Text(
          'AI Tutor',
          style: GoogleFonts.inter(
            color: Colors.white,
            fontWeight: FontWeight.w600,
          ),
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.delete_outline_rounded, color: Colors.white70),
            onPressed: controller.clearChat,
          ),
        ],
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFF1A1A1A),
              Color(0xFF121212),
            ],
          ),
        ),
        child: Row(
          children: [
            // Left Panel
            Obx(() {
              final isExpanded = isLeftPanelExpanded.value;
              return AnimatedContainer(
                duration: Duration(milliseconds: 300),
                width: isExpanded ? 300 : 0,
                child: OverflowBox(
                  maxWidth: 300,
                  child: AnimatedOpacity(
                    duration: Duration(milliseconds: 300),
                    opacity: isExpanded ? 1.0 : 0.0,
                    child: Container(
                      width: 300,
                      margin: EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.05),
                        borderRadius: BorderRadius.circular(24),
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
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(24),
                        child: BackdropFilter(
                          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                          child: Column(
                            children: [
                              // Upload section
                              Container(
                                padding: EdgeInsets.all(16),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Study Materials',
                                      style: GoogleFonts.inter(
                                        fontSize: 20,
                                        fontWeight: FontWeight.w600,
                                        color: Colors.white.withOpacity(0.9),
                                      ),
                                    ),
                                    SizedBox(height: 16),
                                    Obx(() {
                                      final isUploading =
                                          documentController.isUploading.value;
                                      return AnimatedContainer(
                                        duration: Duration(milliseconds: 300),
                                        width: double.infinity,
                                        height: 48,
                                        decoration: BoxDecoration(
                                          color: isUploading
                                              ? Theme.of(context)
                                                  .primaryColor
                                                  .withOpacity(0.1)
                                              : null,
                                          borderRadius:
                                              BorderRadius.circular(12),
                                        ),
                                        child: isUploading
                                            ? Row(
                                                mainAxisAlignment:
                                                    MainAxisAlignment.center,
                                                children: [
                                                  SizedBox(
                                                    width: 20,
                                                    height: 20,
                                                    child:
                                                        CircularProgressIndicator(
                                                      strokeWidth: 2,
                                                      valueColor:
                                                          AlwaysStoppedAnimation<
                                                              Color>(
                                                        Theme.of(context)
                                                            .primaryColor,
                                                      ),
                                                    ),
                                                  ),
                                                  SizedBox(width: 12),
                                                  Text(
                                                    'Uploading...',
                                                    style: GoogleFonts.inter(
                                                      color: Theme.of(context)
                                                          .primaryColor,
                                                      fontWeight:
                                                          FontWeight.w500,
                                                    ),
                                                  ),
                                                ],
                                              )
                                            : ElevatedButton.icon(
                                                icon: Icon(
                                                    Icons.upload_file_rounded),
                                                label: Text('Upload PDF'),
                                                style: ElevatedButton.styleFrom(
                                                  minimumSize:
                                                      Size(double.infinity, 48),
                                                ),
                                                onPressed: documentController
                                                    .uploadDocument,
                                              ),
                                      );
                                    }),
                                  ],
                                ),
                              ),
                              Divider(color: Colors.white.withOpacity(0.1)),
                              // Topics section
                              Expanded(
                                child: Obx(() {
                                  final topicsData =
                                      documentController.topics.value;
                                  final status =
                                      topicsData['status'] as String? ??
                                          'empty';
                                  final topics =
                                      topicsData['topics'] as List? ?? [];

                                  if (status == 'loading') {
                                    return Center(
                                      child: Column(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          CircularProgressIndicator(
                                            valueColor:
                                                AlwaysStoppedAnimation<Color>(
                                              Theme.of(context).primaryColor,
                                            ),
                                          ),
                                          SizedBox(height: 16),
                                          Text(
                                            'Processing document...',
                                            style: GoogleFonts.inter(
                                              color:
                                                  Colors.white.withOpacity(0.7),
                                            ),
                                          ),
                                        ],
                                      ),
                                    );
                                  }

                                  if (status == 'error') {
                                    return Center(
                                      child: Text(
                                        'Error loading topics',
                                        style: GoogleFonts.inter(
                                          color: Colors.red[300],
                                        ),
                                      ),
                                    );
                                  }

                                  if (topics.isEmpty) {
                                    return Center(
                                      child: Text(
                                        'No topics available',
                                        style: GoogleFonts.inter(
                                          color: Colors.white.withOpacity(0.5),
                                        ),
                                      ),
                                    );
                                  }

                                  return ListView.builder(
                                    padding: EdgeInsets.symmetric(
                                        horizontal: 16, vertical: 8),
                                    itemCount: topics.length,
                                    itemBuilder: (context, index) {
                                      final topic = topics[index];
                                      return _buildTopicItem(topic, 0);
                                    },
                                  );
                                }),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              );
            }),

            // Vertical divider
            Obx(() => AnimatedOpacity(
                  duration: Duration(milliseconds: 300),
                  opacity: isLeftPanelExpanded.value ? 1.0 : 0.0,
                  child: Container(
                    width: 1,
                    margin: EdgeInsets.symmetric(vertical: 16),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.white.withOpacity(0.1),
                          Colors.white.withOpacity(0.05),
                          Colors.white.withOpacity(0.1),
                        ],
                      ),
                    ),
                  ),
                )),

            // Chat section
            Expanded(
              child: ChatWidget(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTopicItem(Map<String, dynamic> topic, int level) {
    final hasSubtopics =
        topic['subtopics'] != null && (topic['subtopics'] as List).isNotEmpty;

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          margin: EdgeInsets.symmetric(vertical: 4),
          child: Row(
            children: [
              if (level > 0)
                Container(
                  width: level * 16.0,
                  height: 36,
                  decoration: BoxDecoration(
                    border: Border(
                      left: BorderSide(
                        color: Colors.white.withOpacity(0.1),
                      ),
                    ),
                  ),
                ),
              Expanded(
                child: Row(
                  children: [
                    if (hasSubtopics)
                      Icon(
                        Icons.subdirectory_arrow_right,
                        size: 16,
                        color: Colors.white.withOpacity(0.3),
                      )
                    else
                      SizedBox(width: 16),
                    Expanded(
                      child: Text(
                        topic['title'] ?? '',
                        style: GoogleFonts.inter(
                          color: Colors.white.withOpacity(0.9),
                          fontSize: 14,
                          fontWeight:
                              hasSubtopics ? FontWeight.w500 : FontWeight.w400,
                        ),
                      ),
                    ),
                    TextButton(
                      onPressed: () {
                        controller
                            .sendMessage('Tell me about ${topic['title']}');
                      },
                      child: Text(
                        'Study',
                        style: GoogleFonts.inter(
                          color: Get.theme.primaryColor,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      style: TextButton.styleFrom(
                        padding:
                            EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        minimumSize: Size(0, 0),
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        if (hasSubtopics)
          Padding(
            padding: EdgeInsets.only(left: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: (topic['subtopics'] as List).map((subtopic) {
                return _buildTopicItem(
                    subtopic as Map<String, dynamic>, level + 1);
              }).toList(),
            ),
          ),
      ],
    );
  }
}

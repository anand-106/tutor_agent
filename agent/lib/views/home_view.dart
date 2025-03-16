import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'dart:ui';
import 'package:agent/controllers/chat_controller.dart';
import 'package:agent/controllers/document_controller.dart';
import 'package:agent/controllers/home_view_controller.dart';
import 'package:agent/widgets/chat_widget.dart';
import 'package:agent/widgets/document_upload_widget.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:agent/views/diagram_test_view.dart';
import 'package:agent/widgets/flashcard_widget.dart';
import 'package:agent/widgets/side_panel.dart';

class HomeView extends GetView<ChatController> {
  final DocumentController documentController = Get.put(DocumentController());
  final HomeViewController homeViewController = Get.put(HomeViewController());

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF121212),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.menu, color: Colors.white70),
          onPressed: () => homeViewController.toggleSidePanel(),
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
            icon: Icon(Icons.auto_graph, color: Colors.white70),
            tooltip: 'Test Mermaid Diagrams',
            onPressed: () => Get.to(() => DiagramTestView()),
          ),
        ],
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
            SidePanel(isExpanded: homeViewController.isLeftPanelExpanded),

            // Vertical divider
            Obx(() => AnimatedOpacity(
                  duration: Duration(milliseconds: 300),
                  opacity:
                      homeViewController.isLeftPanelExpanded.value ? 1.0 : 0.0,
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

  Color _getImportanceColor(String importance) {
    switch (importance.toLowerCase()) {
      case 'critical':
        return Colors.red;
      case 'important':
        return Colors.orange;
      case 'good to know':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }
}

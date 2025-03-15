import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'dart:ui';
import 'package:agent/controllers/chat_controller.dart';
import 'package:agent/controllers/document_controller.dart';
import 'package:agent/widgets/chat_widget.dart';
import 'package:agent/widgets/document_upload_widget.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:agent/views/diagram_test_view.dart';
import 'package:agent/widgets/flashcard_widget.dart';

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
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.3),
                        border: Border(
                          right: BorderSide(
                            color: Colors.white.withOpacity(0.1),
                          ),
                        ),
                      ),
                      child: DefaultTabController(
                        length: 2,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              decoration: BoxDecoration(
                                border: Border(
                                  bottom: BorderSide(
                                    color: Colors.white.withOpacity(0.1),
                                  ),
                                ),
                              ),
                              child: TabBar(
                                tabs: [
                                  Tab(
                                    child: Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.center,
                                      children: [
                                        Icon(Icons.book),
                                        SizedBox(width: 8),
                                        Text(
                                          'Materials',
                                          style: GoogleFonts.inter(),
                                        ),
                                      ],
                                    ),
                                  ),
                                  Tab(
                                    child: Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.center,
                                      children: [
                                        Icon(Icons.bookmark),
                                        SizedBox(width: 8),
                                        Text(
                                          'Pinned',
                                          style: GoogleFonts.inter(),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                                indicatorColor: Theme.of(context).primaryColor,
                                indicatorWeight: 3,
                                labelColor: Theme.of(context).primaryColor,
                                unselectedLabelColor:
                                    Colors.white.withOpacity(0.5),
                                labelStyle: GoogleFonts.inter(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                            Expanded(
                              child: TabBarView(
                                children: [
                                  // Study Materials Tab
                                  Padding(
                                    padding: EdgeInsets.all(16),
                                    child: DocumentUploadWidget(),
                                  ),

                                  // Pinned Flashcards Tab
                                  Padding(
                                    padding: EdgeInsets.all(16),
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Expanded(
                                          child: Obx(() {
                                            final pinnedCards =
                                                controller.pinnedFlashcards;
                                            if (pinnedCards.isEmpty) {
                                              return Center(
                                                child: Column(
                                                  mainAxisAlignment:
                                                      MainAxisAlignment.center,
                                                  children: [
                                                    Icon(
                                                      Icons.bookmark_outline,
                                                      size: 48,
                                                      color: Colors.white
                                                          .withOpacity(0.3),
                                                    ),
                                                    SizedBox(height: 16),
                                                    Text(
                                                      'No pinned flashcards',
                                                      style: GoogleFonts.inter(
                                                        color: Colors.white
                                                            .withOpacity(0.5),
                                                      ),
                                                    ),
                                                    SizedBox(height: 8),
                                                    Text(
                                                      'Pin cards while studying to see them here',
                                                      textAlign:
                                                          TextAlign.center,
                                                      style: GoogleFonts.inter(
                                                        color: Colors.white
                                                            .withOpacity(0.3),
                                                        fontSize: 12,
                                                      ),
                                                    ),
                                                  ],
                                                ),
                                              );
                                            }
                                            return ListView.builder(
                                              itemCount: pinnedCards.length,
                                              itemBuilder: (context, index) {
                                                final card = pinnedCards[index];
                                                return Container(
                                                  margin: EdgeInsets.only(
                                                      bottom: 12),
                                                  padding: EdgeInsets.all(12),
                                                  decoration: BoxDecoration(
                                                    color: Theme.of(context)
                                                        .primaryColor
                                                        .withOpacity(0.1),
                                                    borderRadius:
                                                        BorderRadius.circular(
                                                            12),
                                                    border: Border.all(
                                                      color: Theme.of(context)
                                                          .primaryColor
                                                          .withOpacity(0.2),
                                                    ),
                                                  ),
                                                  child: Column(
                                                    crossAxisAlignment:
                                                        CrossAxisAlignment
                                                            .start,
                                                    children: [
                                                      Row(
                                                        mainAxisAlignment:
                                                            MainAxisAlignment
                                                                .spaceBetween,
                                                        children: [
                                                          Expanded(
                                                            child: Text(
                                                              card['front']
                                                                  ['title'],
                                                              style: GoogleFonts
                                                                  .inter(
                                                                fontSize: 14,
                                                                fontWeight:
                                                                    FontWeight
                                                                        .w600,
                                                                color: Colors
                                                                    .white,
                                                              ),
                                                            ),
                                                          ),
                                                          IconButton(
                                                            icon: Icon(
                                                                Icons.push_pin,
                                                                color: Theme.of(
                                                                        context)
                                                                    .primaryColor,
                                                                size: 18),
                                                            onPressed: () {
                                                              controller
                                                                  .unpinCard(
                                                                      card);
                                                            },
                                                            padding:
                                                                EdgeInsets.zero,
                                                            constraints:
                                                                BoxConstraints(),
                                                            tooltip: 'Unpin',
                                                          ),
                                                        ],
                                                      ),
                                                      SizedBox(height: 8),
                                                      Container(
                                                        padding: EdgeInsets
                                                            .symmetric(
                                                                horizontal: 8,
                                                                vertical: 4),
                                                        decoration:
                                                            BoxDecoration(
                                                          color: _getImportanceColor(
                                                                  card[
                                                                      'importance'])
                                                              .withOpacity(0.1),
                                                          borderRadius:
                                                              BorderRadius
                                                                  .circular(4),
                                                        ),
                                                        child: Text(
                                                          card['importance'],
                                                          style:
                                                              GoogleFonts.inter(
                                                            fontSize: 12,
                                                            color: _getImportanceColor(
                                                                card[
                                                                    'importance']),
                                                          ),
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                );
                                              },
                                            );
                                          }),
                                        ),
                                      ],
                                    ),
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

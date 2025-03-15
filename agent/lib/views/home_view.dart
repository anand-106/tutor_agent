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
                        length: 3,
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
                                isScrollable: false,
                                tabs: [
                                  Tab(
                                    child: Container(
                                      constraints: BoxConstraints(maxWidth: 90),
                                      child: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Icon(Icons.upload_file, size: 18),
                                          SizedBox(width: 4),
                                          Flexible(
                                            child: Text(
                                              'Upload',
                                              style: GoogleFonts.inter(
                                                  fontSize: 13),
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                  Tab(
                                    child: Container(
                                      constraints: BoxConstraints(maxWidth: 90),
                                      child: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Icon(Icons.topic, size: 18),
                                          SizedBox(width: 4),
                                          Flexible(
                                            child: Text(
                                              'Topics',
                                              style: GoogleFonts.inter(
                                                  fontSize: 13),
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                  Tab(
                                    child: Container(
                                      constraints: BoxConstraints(maxWidth: 90),
                                      child: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Icon(Icons.bookmark, size: 18),
                                          SizedBox(width: 4),
                                          Flexible(
                                            child: Text(
                                              'Pinned',
                                              style: GoogleFonts.inter(
                                                  fontSize: 13),
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                        ],
                                      ),
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
                                  // Upload Tab
                                  Padding(
                                    padding: EdgeInsets.all(16),
                                    child: DocumentUploadWidget(),
                                  ),

                                  // Topics Tab
                                  Padding(
                                    padding: EdgeInsets.all(16),
                                    child: Obx(() {
                                      final topicsData =
                                          documentController.topics.value;

                                      if (topicsData['status'] == 'loading') {
                                        return Center(
                                          child: CircularProgressIndicator(
                                            valueColor:
                                                AlwaysStoppedAnimation<Color>(
                                              Theme.of(context).primaryColor,
                                            ),
                                          ),
                                        );
                                      }

                                      if (topicsData['status'] == 'error') {
                                        return Center(
                                          child: Text(
                                            topicsData['message'] ??
                                                'Error loading topics',
                                            style: GoogleFonts.inter(
                                              color:
                                                  Colors.red.withOpacity(0.8),
                                            ),
                                          ),
                                        );
                                      }

                                      final topics =
                                          topicsData['topics'] as List;

                                      if (topics.isEmpty) {
                                        return Center(
                                          child: Column(
                                            mainAxisAlignment:
                                                MainAxisAlignment.center,
                                            children: [
                                              Icon(
                                                Icons.topic_outlined,
                                                size: 48,
                                                color: Colors.white
                                                    .withOpacity(0.3),
                                              ),
                                              SizedBox(height: 16),
                                              Text(
                                                'No topics available',
                                                style: GoogleFonts.inter(
                                                  color: Colors.white
                                                      .withOpacity(0.5),
                                                ),
                                              ),
                                              SizedBox(height: 8),
                                              Text(
                                                'Upload a document to see topics',
                                                textAlign: TextAlign.center,
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
                                        itemCount: topics.length,
                                        itemBuilder: (context, index) {
                                          final topic = topics[index];
                                          return Container(
                                            margin: EdgeInsets.only(bottom: 12),
                                            padding: EdgeInsets.all(12),
                                            decoration: BoxDecoration(
                                              color: Theme.of(context)
                                                  .primaryColor
                                                  .withOpacity(0.1),
                                              borderRadius:
                                                  BorderRadius.circular(12),
                                              border: Border.all(
                                                color: Theme.of(context)
                                                    .primaryColor
                                                    .withOpacity(0.2),
                                              ),
                                            ),
                                            child: Column(
                                              crossAxisAlignment:
                                                  CrossAxisAlignment.start,
                                              children: [
                                                Row(
                                                  mainAxisAlignment:
                                                      MainAxisAlignment
                                                          .spaceBetween,
                                                  children: [
                                                    Expanded(
                                                      child: Text(
                                                        topic['title'] ??
                                                            'Untitled Topic',
                                                        style:
                                                            GoogleFonts.inter(
                                                          fontSize: 14,
                                                          fontWeight:
                                                              FontWeight.w600,
                                                          color: Colors.white,
                                                        ),
                                                      ),
                                                    ),
                                                    ElevatedButton.icon(
                                                      icon: Icon(Icons.school,
                                                          size: 16),
                                                      label: Text('Study'),
                                                      onPressed: () {
                                                        // TODO: Implement study functionality
                                                      },
                                                      style: ElevatedButton
                                                          .styleFrom(
                                                        padding: EdgeInsets
                                                            .symmetric(
                                                          horizontal: 12,
                                                          vertical: 8,
                                                        ),
                                                        textStyle:
                                                            GoogleFonts.inter(
                                                          fontSize: 12,
                                                          fontWeight:
                                                              FontWeight.w500,
                                                        ),
                                                      ),
                                                    ),
                                                  ],
                                                ),
                                                if (topic['content'] !=
                                                    null) ...[
                                                  SizedBox(height: 8),
                                                  Text(
                                                    topic['content'],
                                                    style: GoogleFonts.inter(
                                                      fontSize: 12,
                                                      color: Colors.white
                                                          .withOpacity(0.7),
                                                    ),
                                                  ),
                                                ],
                                                if (topic['subtopics'] !=
                                                    null) ...[
                                                  SizedBox(height: 12),
                                                  ...List<Widget>.from(
                                                    (topic['subtopics'] as List)
                                                        .map(
                                                      (subtopic) {
                                                        if (subtopic is Map) {
                                                          return Container(
                                                            margin:
                                                                EdgeInsets.only(
                                                                    left: 16),
                                                            child: Stack(
                                                              children: [
                                                                // Vertical connection line
                                                                Positioned(
                                                                  left: 2,
                                                                  top: 0,
                                                                  bottom: 0,
                                                                  width: 2,
                                                                  child:
                                                                      Container(
                                                                    color: Theme.of(
                                                                            context)
                                                                        .primaryColor
                                                                        .withOpacity(
                                                                            0.3),
                                                                  ),
                                                                ),
                                                                // Horizontal connection line
                                                                Positioned(
                                                                  left: 2,
                                                                  top: 12,
                                                                  width: 12,
                                                                  height: 2,
                                                                  child:
                                                                      Container(
                                                                    color: Theme.of(
                                                                            context)
                                                                        .primaryColor
                                                                        .withOpacity(
                                                                            0.3),
                                                                  ),
                                                                ),
                                                                Padding(
                                                                  padding:
                                                                      EdgeInsets
                                                                          .only(
                                                                    left: 24,
                                                                    bottom: 12,
                                                                  ),
                                                                  child: Row(
                                                                    mainAxisAlignment:
                                                                        MainAxisAlignment
                                                                            .spaceBetween,
                                                                    children: [
                                                                      Expanded(
                                                                        child:
                                                                            Column(
                                                                          crossAxisAlignment:
                                                                              CrossAxisAlignment.start,
                                                                          children: [
                                                                            Text(
                                                                              subtopic['title'] ?? '',
                                                                              style: GoogleFonts.inter(
                                                                                fontSize: 13,
                                                                                fontWeight: FontWeight.w500,
                                                                                color: Colors.white.withOpacity(0.9),
                                                                              ),
                                                                            ),
                                                                            if (subtopic['content'] !=
                                                                                null) ...[
                                                                              SizedBox(height: 4),
                                                                              Text(
                                                                                subtopic['content'],
                                                                                style: GoogleFonts.inter(
                                                                                  fontSize: 12,
                                                                                  color: Colors.white.withOpacity(0.7),
                                                                                ),
                                                                              ),
                                                                            ],
                                                                          ],
                                                                        ),
                                                                      ),
                                                                      ElevatedButton
                                                                          .icon(
                                                                        icon: Icon(
                                                                            Icons
                                                                                .school,
                                                                            size:
                                                                                14),
                                                                        label: Text(
                                                                            'Study'),
                                                                        onPressed:
                                                                            () {
                                                                          // TODO: Implement study functionality
                                                                        },
                                                                        style: ElevatedButton
                                                                            .styleFrom(
                                                                          padding:
                                                                              EdgeInsets.symmetric(
                                                                            horizontal:
                                                                                8,
                                                                            vertical:
                                                                                4,
                                                                          ),
                                                                          textStyle:
                                                                              GoogleFonts.inter(
                                                                            fontSize:
                                                                                11,
                                                                            fontWeight:
                                                                                FontWeight.w500,
                                                                          ),
                                                                        ),
                                                                      ),
                                                                    ],
                                                                  ),
                                                                ),
                                                              ],
                                                            ),
                                                          );
                                                        } else {
                                                          return Container(
                                                            margin:
                                                                EdgeInsets.only(
                                                                    left: 16),
                                                            child: Stack(
                                                              children: [
                                                                // Vertical connection line
                                                                Positioned(
                                                                  left: 2,
                                                                  top: 0,
                                                                  bottom: 0,
                                                                  width: 2,
                                                                  child:
                                                                      Container(
                                                                    color: Theme.of(
                                                                            context)
                                                                        .primaryColor
                                                                        .withOpacity(
                                                                            0.3),
                                                                  ),
                                                                ),
                                                                // Horizontal connection line
                                                                Positioned(
                                                                  left: 2,
                                                                  top: 12,
                                                                  width: 12,
                                                                  height: 2,
                                                                  child:
                                                                      Container(
                                                                    color: Theme.of(
                                                                            context)
                                                                        .primaryColor
                                                                        .withOpacity(
                                                                            0.3),
                                                                  ),
                                                                ),
                                                                Padding(
                                                                  padding:
                                                                      EdgeInsets
                                                                          .only(
                                                                    left: 24,
                                                                    bottom: 12,
                                                                  ),
                                                                  child: Row(
                                                                    mainAxisAlignment:
                                                                        MainAxisAlignment
                                                                            .spaceBetween,
                                                                    children: [
                                                                      Expanded(
                                                                        child:
                                                                            Text(
                                                                          subtopic
                                                                              .toString(),
                                                                          style:
                                                                              GoogleFonts.inter(
                                                                            fontSize:
                                                                                12,
                                                                            color:
                                                                                Colors.white.withOpacity(0.7),
                                                                          ),
                                                                        ),
                                                                      ),
                                                                      ElevatedButton
                                                                          .icon(
                                                                        icon: Icon(
                                                                            Icons
                                                                                .school,
                                                                            size:
                                                                                14),
                                                                        label: Text(
                                                                            'Study'),
                                                                        onPressed:
                                                                            () {
                                                                          // TODO: Implement study functionality
                                                                        },
                                                                        style: ElevatedButton
                                                                            .styleFrom(
                                                                          padding:
                                                                              EdgeInsets.symmetric(
                                                                            horizontal:
                                                                                8,
                                                                            vertical:
                                                                                4,
                                                                          ),
                                                                          textStyle:
                                                                              GoogleFonts.inter(
                                                                            fontSize:
                                                                                11,
                                                                            fontWeight:
                                                                                FontWeight.w500,
                                                                          ),
                                                                        ),
                                                                      ),
                                                                    ],
                                                                  ),
                                                                ),
                                                              ],
                                                            ),
                                                          );
                                                        }
                                                      },
                                                    ),
                                                  ),
                                                ],
                                              ],
                                            ),
                                          );
                                        },
                                      );
                                    }),
                                  ),

                                  // Pinned Flashcards Tab
                                  Padding(
                                    padding: EdgeInsets.all(16),
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
                                                textAlign: TextAlign.center,
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
                                            margin: EdgeInsets.only(bottom: 12),
                                            padding: EdgeInsets.all(12),
                                            decoration: BoxDecoration(
                                              color: Theme.of(context)
                                                  .primaryColor
                                                  .withOpacity(0.1),
                                              borderRadius:
                                                  BorderRadius.circular(12),
                                              border: Border.all(
                                                color: Theme.of(context)
                                                    .primaryColor
                                                    .withOpacity(0.2),
                                              ),
                                            ),
                                            child: InkWell(
                                              onTap: () {
                                                showDialog(
                                                  context: context,
                                                  builder: (context) => Dialog(
                                                    backgroundColor:
                                                        Colors.transparent,
                                                    child: Container(
                                                      width: 600,
                                                      constraints:
                                                          BoxConstraints(
                                                              maxHeight: 400),
                                                      decoration: BoxDecoration(
                                                        color:
                                                            Color(0xFF1E1E1E),
                                                        borderRadius:
                                                            BorderRadius
                                                                .circular(16),
                                                        border: Border.all(
                                                          color: Colors.white
                                                              .withOpacity(0.1),
                                                        ),
                                                      ),
                                                      child: Column(
                                                        mainAxisSize:
                                                            MainAxisSize.min,
                                                        children: [
                                                          // Header
                                                          Container(
                                                            padding:
                                                                EdgeInsets.all(
                                                                    16),
                                                            decoration:
                                                                BoxDecoration(
                                                              border: Border(
                                                                bottom:
                                                                    BorderSide(
                                                                  color: Colors
                                                                      .white
                                                                      .withOpacity(
                                                                          0.1),
                                                                ),
                                                              ),
                                                            ),
                                                            child: Row(
                                                              mainAxisAlignment:
                                                                  MainAxisAlignment
                                                                      .spaceBetween,
                                                              children: [
                                                                Row(
                                                                  children: [
                                                                    Container(
                                                                      padding:
                                                                          EdgeInsets
                                                                              .symmetric(
                                                                        horizontal:
                                                                            8,
                                                                        vertical:
                                                                            4,
                                                                      ),
                                                                      decoration:
                                                                          BoxDecoration(
                                                                        color:
                                                                            _getImportanceColor(
                                                                          card[
                                                                              'importance'],
                                                                        ).withOpacity(0.1),
                                                                        borderRadius:
                                                                            BorderRadius.circular(4),
                                                                      ),
                                                                      child:
                                                                          Text(
                                                                        card[
                                                                            'importance'],
                                                                        style: GoogleFonts
                                                                            .inter(
                                                                          fontSize:
                                                                              12,
                                                                          color:
                                                                              _getImportanceColor(
                                                                            card['importance'],
                                                                          ),
                                                                        ),
                                                                      ),
                                                                    ),
                                                                  ],
                                                                ),
                                                                IconButton(
                                                                  icon: Icon(Icons
                                                                      .close),
                                                                  onPressed: () =>
                                                                      Navigator.pop(
                                                                          context),
                                                                  color: Colors
                                                                      .white
                                                                      .withOpacity(
                                                                          0.5),
                                                                ),
                                                              ],
                                                            ),
                                                          ),
                                                          // Content
                                                          Expanded(
                                                            child:
                                                                SingleChildScrollView(
                                                              padding:
                                                                  EdgeInsets
                                                                      .all(24),
                                                              child: Column(
                                                                crossAxisAlignment:
                                                                    CrossAxisAlignment
                                                                        .start,
                                                                children: [
                                                                  // Front
                                                                  Text(
                                                                    'Front',
                                                                    style: GoogleFonts
                                                                        .inter(
                                                                      fontSize:
                                                                          14,
                                                                      color: Colors
                                                                          .white
                                                                          .withOpacity(
                                                                              0.5),
                                                                    ),
                                                                  ),
                                                                  SizedBox(
                                                                      height:
                                                                          8),
                                                                  Text(
                                                                    card['front']
                                                                        [
                                                                        'title'],
                                                                    style: GoogleFonts
                                                                        .inter(
                                                                      fontSize:
                                                                          18,
                                                                      fontWeight:
                                                                          FontWeight
                                                                              .w600,
                                                                      color: Colors
                                                                          .white,
                                                                    ),
                                                                  ),
                                                                  SizedBox(
                                                                      height:
                                                                          12),
                                                                  ...card['front']
                                                                          [
                                                                          'points']
                                                                      .map<
                                                                          Widget>(
                                                                        (point) =>
                                                                            Padding(
                                                                          padding:
                                                                              EdgeInsets.only(bottom: 8),
                                                                          child:
                                                                              Row(
                                                                            crossAxisAlignment:
                                                                                CrossAxisAlignment.start,
                                                                            children: [
                                                                              Text(
                                                                                '• ',
                                                                                style: GoogleFonts.inter(
                                                                                  color: Theme.of(context).primaryColor,
                                                                                ),
                                                                              ),
                                                                              Expanded(
                                                                                child: Text(
                                                                                  point,
                                                                                  style: GoogleFonts.inter(
                                                                                    color: Colors.white.withOpacity(0.9),
                                                                                  ),
                                                                                ),
                                                                              ),
                                                                            ],
                                                                          ),
                                                                        ),
                                                                      )
                                                                      .toList(),
                                                                  SizedBox(
                                                                      height:
                                                                          24),
                                                                  // Back
                                                                  Text(
                                                                    'Back',
                                                                    style: GoogleFonts
                                                                        .inter(
                                                                      fontSize:
                                                                          14,
                                                                      color: Colors
                                                                          .white
                                                                          .withOpacity(
                                                                              0.5),
                                                                    ),
                                                                  ),
                                                                  SizedBox(
                                                                      height:
                                                                          8),
                                                                  Text(
                                                                    card['back']
                                                                        [
                                                                        'title'],
                                                                    style: GoogleFonts
                                                                        .inter(
                                                                      fontSize:
                                                                          18,
                                                                      fontWeight:
                                                                          FontWeight
                                                                              .w600,
                                                                      color: Colors
                                                                          .white,
                                                                    ),
                                                                  ),
                                                                  SizedBox(
                                                                      height:
                                                                          12),
                                                                  ...card['back']
                                                                          [
                                                                          'points']
                                                                      .map<
                                                                          Widget>(
                                                                        (point) =>
                                                                            Padding(
                                                                          padding:
                                                                              EdgeInsets.only(bottom: 8),
                                                                          child:
                                                                              Row(
                                                                            crossAxisAlignment:
                                                                                CrossAxisAlignment.start,
                                                                            children: [
                                                                              Text(
                                                                                '• ',
                                                                                style: GoogleFonts.inter(
                                                                                  color: Theme.of(context).primaryColor,
                                                                                ),
                                                                              ),
                                                                              Expanded(
                                                                                child: Text(
                                                                                  point,
                                                                                  style: GoogleFonts.inter(
                                                                                    color: Colors.white.withOpacity(0.9),
                                                                                  ),
                                                                                ),
                                                                              ),
                                                                            ],
                                                                          ),
                                                                        ),
                                                                      )
                                                                      .toList(),
                                                                ],
                                                              ),
                                                            ),
                                                          ),
                                                        ],
                                                      ),
                                                    ),
                                                  ),
                                                );
                                              },
                                              child: Column(
                                                crossAxisAlignment:
                                                    CrossAxisAlignment.start,
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
                                                          style:
                                                              GoogleFonts.inter(
                                                            fontSize: 14,
                                                            fontWeight:
                                                                FontWeight.w600,
                                                            color: Colors.white,
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
                                                              .unpinCard(card);
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
                                                    padding:
                                                        EdgeInsets.symmetric(
                                                            horizontal: 8,
                                                            vertical: 4),
                                                    decoration: BoxDecoration(
                                                      color: _getImportanceColor(
                                                              card[
                                                                  'importance'])
                                                          .withOpacity(0.1),
                                                      borderRadius:
                                                          BorderRadius.circular(
                                                              4),
                                                    ),
                                                    child: Text(
                                                      card['importance'],
                                                      style: GoogleFonts.inter(
                                                        fontSize: 12,
                                                        color: _getImportanceColor(
                                                            card['importance']),
                                                      ),
                                                    ),
                                                  ),
                                                ],
                                              ),
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

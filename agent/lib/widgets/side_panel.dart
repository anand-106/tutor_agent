import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:agent/widgets/upload_tab.dart';
import 'package:agent/widgets/topics_tab.dart';
import 'package:agent/widgets/pinned_tab.dart';
import 'package:agent/widgets/progress_dashboard.dart';

class SidePanel extends StatelessWidget {
  final RxBool isExpanded;

  const SidePanel({
    Key? key,
    required this.isExpanded,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      final isExpandedValue = isExpanded.value;
      return AnimatedContainer(
        duration: Duration(milliseconds: 300),
        width: isExpandedValue ? 300 : 0,
        child: OverflowBox(
          maxWidth: 300,
          child: AnimatedOpacity(
            duration: Duration(milliseconds: 300),
            opacity: isExpandedValue ? 1.0 : 0.0,
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
                length: 4,
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
                          _buildTab(Icons.upload_file, 'Upload'),
                          _buildTab(Icons.topic, 'Topics'),
                          _buildTab(Icons.bookmark, 'Pinned'),
                          _buildTab(Icons.analytics, 'Progress'),
                        ],
                        indicatorColor: Theme.of(context).primaryColor,
                        indicatorWeight: 3,
                        labelColor: Theme.of(context).primaryColor,
                        unselectedLabelColor: Colors.white.withOpacity(0.5),
                        labelStyle: GoogleFonts.inter(
                          fontWeight: FontWeight.w600,
                        ),
                        padding: EdgeInsets.symmetric(horizontal: 8),
                        labelPadding: EdgeInsets.symmetric(horizontal: 16),
                      ),
                    ),
                    Expanded(
                      child: TabBarView(
                        children: [
                          UploadTab(),
                          TopicsTab(),
                          PinnedTab(),
                          ProgressDashboard(),
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
    });
  }

  Widget _buildTab(IconData icon, String text) {
    return Tab(
      height: 48,
      icon: Icon(icon, size: 24),
      // Tooltip to show the tab name on hover
      child: Tooltip(
        message: text,
        child: Container(),
      ),
    );
  }
}

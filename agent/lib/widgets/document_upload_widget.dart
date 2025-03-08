import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:agent/controllers/document_controller.dart';
import 'package:google_fonts/google_fonts.dart';

class DocumentUploadWidget extends StatelessWidget {
  final DocumentController controller = Get.find();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: EdgeInsets.all(20),
          child: Text(
            'Upload Study Materials',
            style: GoogleFonts.inter(
              fontSize: 20,
              fontWeight: FontWeight.w600,
              color: Colors.white.withOpacity(0.9),
            ),
          ),
        ),

        // Upload button
        Obx(
          () => controller.isUploading.value
              ? CircularProgressIndicator(
                  valueColor: AlwaysStoppedAnimation<Color>(
                    Theme.of(context).primaryColor,
                  ),
                )
              : Container(
                  margin: EdgeInsets.symmetric(horizontal: 20),
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    icon: Icon(Icons.upload_file_rounded, color: Colors.white),
                    label: Text(
                      'Upload PDF',
                      style: GoogleFonts.inter(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                      ),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Theme.of(context).primaryColor,
                      padding: EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      elevation: 0,
                    ),
                    onPressed: controller.uploadDocument,
                  ),
                ),
        ),

        SizedBox(height: 20),

        // Document list
        Expanded(
          child: Obx(
            () => ListView.builder(
              padding: EdgeInsets.symmetric(horizontal: 16),
              itemCount: controller.documents.length,
              itemBuilder: (context, index) {
                final doc = controller.documents[index];
                return Container(
                  margin: EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.08),
                    ),
                  ),
                  child: ListTile(
                    leading: Container(
                      padding: EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Theme.of(context).primaryColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Icon(
                        Icons.description_rounded,
                        color: Theme.of(context).primaryColor,
                      ),
                    ),
                    title: Text(
                      doc.name,
                      style: GoogleFonts.inter(
                        color: Colors.white.withOpacity(0.9),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    subtitle: Text(
                      doc.uploadTime.toString(),
                      style: GoogleFonts.inter(
                        color: Colors.white.withOpacity(0.5),
                        fontSize: 12,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ),
      ],
    );
  }
}

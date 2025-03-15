import 'package:flutter/material.dart';
import 'package:agent/widgets/document_upload_widget.dart';

class UploadTab extends StatelessWidget {
  const UploadTab({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: DocumentUploadWidget(),
      ),
    );
  }
}

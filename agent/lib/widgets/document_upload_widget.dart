import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:agent/controllers/document_controller.dart';

class DocumentUploadWidget extends StatelessWidget {
  final DocumentController controller = Get.find();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: EdgeInsets.all(16.0),
          child: Text(
            'Upload Study Materials',
            style: Theme.of(context).textTheme.titleLarge,
          ),
        ),

        // Upload button
        Obx(
          () => controller.isUploading.value
              ? CircularProgressIndicator()
              : ElevatedButton.icon(
                  icon: Icon(Icons.upload_file),
                  label: Text('Upload PDF'),
                  onPressed: controller.uploadDocument,
                ),
        ),

        // Document list
        Expanded(
          child: Obx(() => ListView.builder(
                itemCount: controller.documents.length,
                itemBuilder: (context, index) {
                  final doc = controller.documents[index];
                  return ListTile(
                    leading: Icon(Icons.description),
                    title: Text(doc.name),
                    subtitle: Text(doc.uploadTime.toString()),
                  );
                },
              )),
        ),
      ],
    );
  }
}

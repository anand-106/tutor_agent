import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:agent/views/home_view.dart';
import 'package:agent/controllers/theme_controller.dart';
import 'package:agent/services/api_service.dart';
import 'package:agent/controllers/chat_controller.dart';

void main() {
  // Initialize services and controllers
  Get.put(ApiService());
  Get.put(ChatController());

  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  final ThemeController themeController = Get.put(ThemeController());

  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: 'AI Tutor',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: HomeView(),
      debugShowCheckedModeBanner: false,
    );
  }
}

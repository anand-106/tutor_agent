import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:agent/views/home_view.dart';
import 'package:agent/controllers/theme_controller.dart';
import 'package:agent/services/api_service.dart';

void main() {
  // Initialize services
  Get.put(ApiService());

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

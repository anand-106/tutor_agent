import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:agent/views/home_view.dart';
import 'package:agent/controllers/theme_controller.dart';
import 'package:agent/services/api_service.dart';
import 'package:agent/controllers/chat_controller.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize services and controllers
  await Get.putAsync(() => ApiService().init());
  Get.put(ChatController());

  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  final ThemeController themeController = Get.put(ThemeController());

  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: 'AI Tutor',
      home: HomeView(),
      theme: ThemeData(
        brightness: Brightness.dark,
        primaryColor: Color(0xFF2196F3),
        scaffoldBackgroundColor: Color(0xFF121212),
        colorScheme: ColorScheme.dark(
          primary: Color(0xFF2196F3),
          secondary: Color(0xFF64B5F6),
          surface: Colors.white.withOpacity(0.05),
          background: Color(0xFF121212),
          error: Colors.red[400]!,
        ),
        cardColor: Colors.white.withOpacity(0.05),
        dividerColor: Colors.white.withOpacity(0.1),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: Color(0xFF2196F3),
            foregroundColor: Colors.white,
            elevation: 0,
            padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
        textButtonTheme: TextButtonThemeData(
          style: TextButton.styleFrom(
            foregroundColor: Color(0xFF2196F3),
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        ),
        iconTheme: IconThemeData(
          color: Colors.white.withOpacity(0.9),
        ),
        textTheme: TextTheme(
          titleLarge: TextStyle(
            color: Colors.white.withOpacity(0.9),
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
          titleMedium: TextStyle(
            color: Colors.white.withOpacity(0.9),
            fontSize: 16,
            fontWeight: FontWeight.w500,
          ),
          bodyLarge: TextStyle(
            color: Colors.white.withOpacity(0.9),
            fontSize: 16,
          ),
          bodyMedium: TextStyle(
            color: Colors.white.withOpacity(0.7),
            fontSize: 14,
          ),
        ),
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      debugShowCheckedModeBanner: false,
    );
  }
}

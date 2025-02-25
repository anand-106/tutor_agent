import 'package:dio/dio.dart' as dio;
import 'package:get/get.dart';
import 'package:file_picker/file_picker.dart';

class ApiService extends GetxService {
  late final dio.Dio _dio;
  final String baseUrl = 'http://127.0.0.1:8000/api';

  @override
  void onInit() {
    super.onInit();
    _dio = dio.Dio(dio.BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: Duration(seconds: 60),
      receiveTimeout: Duration(seconds: 60),
      sendTimeout: Duration(seconds: 60),
      validateStatus: (status) => true,
    ));

    _dio.interceptors.add(dio.LogInterceptor(
      requestBody: true,
      responseBody: true,
    ));
  }

  Future<String> sendChatMessage(String message) async {
    try {
      final response = await _dio.post('/chat', data: {
        'text': message,
      });
      return response.data['response'];
    } catch (e) {
      throw 'Failed to send message: $e';
    }
  }

  Future<void> uploadDocument(PlatformFile file) async {
    try {
      final formData = dio.FormData.fromMap({
        'file': await dio.MultipartFile.fromBytes(
          file.bytes!,
          filename: file.name,
        ),
      });

      final response = await _dio.post(
        '/upload',
        data: formData,
      );

      if (response.statusCode != 200) {
        throw 'Upload failed with status: ${response.statusCode}, message: ${response.data}';
      }
    } on dio.DioException catch (e) {
      print('DioError: ${e.message}, ${e.response?.data}');
      throw 'Network error: ${e.message}';
    } catch (e) {
      print('Error: $e');
      throw 'Failed to upload document: $e';
    }
  }
}

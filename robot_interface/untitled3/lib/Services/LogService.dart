import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';
import '../models/products.dart';

class LogService {
  static String beUrl = dotenv.env['BE_URL'] ?? '';
  static String idRobot = dotenv.env['ID_ROBOT'] ?? '';

  static Future<bool> postLogService(String message) async {
    try {
      final url = Uri.parse('$beUrl/logs/'); // adjust endpoint path if needed

      final body = jsonEncode({
        "message": message,
        "robot_id": int.parse(idRobot),
        "created_at": DateTime.now().toUtc().toIso8601String(),
      });

      final response = await http.post(
        url,
        headers: {
          "Content-Type": "application/json",
        },
        body: body,
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        print("✅ Log sent successfully: ${response.body}");
        return true;
      } else {
        print("⚠️ Failed to send log: ${response.statusCode}");
        print("Response: ${response.body}");
        return false;
      }
    } catch (e) {
      print("❌ Error sending log: $e");
      return false;
    }
  }

}

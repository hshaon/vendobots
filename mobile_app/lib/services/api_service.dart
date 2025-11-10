import 'dart:convert';
import 'dart:io' show Platform; // Used to check the OS
import 'package:flutter/foundation.dart' show kIsWeb; // Used to check if running on Web
import 'package:http/http.dart' as http;
import '../models/robot.dart';
import '../models/inventory_item.dart';
import '../models/robot_log.dart';

class ApiService {
  
  // This 'getter' automatically selects the correct IP address
  // NOTE: Assuming backend runs on the default port 8000
  String get baseUrl {
    if (kIsWeb) {
      // Running in a web browser (like Chrome)
      return "http://127.0.0.1:8000";
    } else if (Platform.isAndroid) {
      // Running on an Android Emulator
      return "http://10.0.2.2:8000";
    } else if (Platform.isWindows || Platform.isLinux || Platform.isMacOS) {
      // Running on a PC (Desktop app)
      return "http://127.0.0.1:8000";
    } else if (Platform.isIOS) {
      // Running on an iOS Simulator
      return "http://127.0.0.1:8000";
    }

    // Default fallback (shouldn't be reached)
    return "http://127.0.0.1:8000";
  }

  // Fetches all robots (from GET /robots)
  Future<List<Robot>> getRobots() async {
    final response = await http.get(Uri.parse('$baseUrl/robots/'));

    if (response.statusCode == 200) {
      List<dynamic> jsonResponse = json.decode(response.body);
      // This now correctly parses the x_coord and y_coord fields
      return jsonResponse.map((robot) => Robot.fromJson(robot)).toList();
    } else {
      throw Exception('Failed to load robots');
    }
  }

  // Fetches all inventory items (from GET /inventory)
  Future<List<InventoryItem>> getInventoryItems() async {
    final response = await http.get(Uri.parse('$baseUrl/inventory/'));

    if (response.statusCode == 200) {
      List<dynamic> jsonResponse = json.decode(response.body);
      return jsonResponse.map((item) => InventoryItem.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load inventory');
    }
  }

  // Fetches all logs (from GET /logs)
  Future<List<RobotLog>> getLogs() async {
    final response = await http.get(Uri.parse('$baseUrl/logs/'));
    if (response.statusCode == 200) {
      List<dynamic> jsonResponse = json.decode(response.body);
      return jsonResponse.map((log) => RobotLog.fromJson(log)).toList();
    } else {
      throw Exception('Failed to load logs');
    }
  }

  // --- NEW DELIVERY RECORD ENDPOINT (POST /deliveryrecords/) ---
  Future<void> createDeliveryRecord({
    required int robotId,
    required String message,
    required String address,
    required String status,
    // Note: Nullable because initial robot coordinates might be null (though 0.0 is safer)
    required double? startX, 
    required double? startY,
    required double destX,
    required double destY,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/deliveryrecords/'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'robot_id': robotId,
        'message': message,
        'address': address,
        // Placeholder values for inventory and quantity, as they aren't used for waypoint setting
        'inventory_ids': "N/A", 
        'quantity': "N/A", 
        'status': status,
        // Use ?? 0.0 to ensure a non-null float is sent to FastAPI
        'start_x': startX ?? 0.0,
        'start_y': startY ?? 0.0,
        'dest_x': destX,
        'dest_y': destY,
      }),
    );

    if (response.statusCode != 200) {
      final responseBody = json.decode(response.body);
      throw Exception('Failed to create delivery record: ${responseBody['detail']}');
    }
  }

  // --- NEW ROBOT LOCATION UPDATE ENDPOINT (PUT /robots/{id}/location) ---
  // This is used for simulating the robot's movement or receiving ROS updates
  Future<void> updateRobotLocation({
    required int robotId,
    required double xCoord,
    required double yCoord,
  }) async {
    final response = await http.put(
      Uri.parse('$baseUrl/robots/$robotId/location'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'x_coord': xCoord,
        'y_coord': yCoord,
      }),
    );

    if (response.statusCode != 200) {
      final responseBody = json.decode(response.body);
      throw Exception('Failed to update robot location: ${responseBody['detail']}');
    }
  }
}
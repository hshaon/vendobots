import 'dart:convert';
import 'dart:io' show Platform; // Used to check the OS
import 'package:flutter/foundation.dart' show kIsWeb; // Used to check if running on Web
import 'package:http/http.dart' as http;
import '../models/robot.dart';
import '../models/inventory_item.dart';
import '../models/robot_log.dart';
import '../models/delivery_record.dart';

class ApiService {
  // This 'getter' automatically selects the correct IP address
  String get baseUrl {
    // Replace '192.168.1.15' with YOUR computer's actual local IP address
    const String localServerIp = "10.22.27.115"; 

    if (kIsWeb) {
      return "http://localhost:8000"; // Web usually works with localhost if on same machine
    } else if (Platform.isAndroid) {
      // If using a REAL device, use the computer's IP. 
      // If using an emulator, '10.0.2.2' is fine, but real IP works for both.
      return "http://$localServerIp:8000"; 
    } else if (Platform.isIOS) {
      // Physical iOS devices need the computer's IP
      return "http://$localServerIp:8000";
    } else {
      // Fallback for Desktop apps
      return "http://localhost:8000";
    }
  }

  // --- NOTE ON REAL DEVICES ---
  // If you run this on a REAL Android phone (not an emulator),
  // you must:
  // 1. Find your PC's local network IP (e.g., 192.168.1.10)
  // 2. Run uvicorn using: uvicorn app.main:app --reload --host 0.0.0.0
  // 3. Change the IP for Android to: "http://192.168.1.10:8000"

  // Fetches all robots (from GET /robots)
  Future<List<Robot>> getRobots() async {
    final response = await http.get(Uri.parse('$baseUrl/robots/'));

    if (response.statusCode == 200) {
      List<dynamic> jsonResponse = json.decode(response.body);
      return jsonResponse.map((robot) => Robot.fromJson(robot)).toList();
    } else {
      throw Exception('Failed to load robots');
    }
  }

  Future<List<InventoryItem>> getInventoryItems() async {
    final response = await http.get(Uri.parse('$baseUrl/inventory/'));

    if (response.statusCode == 200) {
      List<dynamic> jsonResponse = json.decode(response.body);
      return jsonResponse.map((item) => InventoryItem.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load inventory');
    }
  }

  Future<List<RobotLog>> getLogs() async {
    final response = await http.get(Uri.parse('$baseUrl/logs/'));
    if (response.statusCode == 200) {
      List<dynamic> jsonResponse = json.decode(response.body);
      return jsonResponse.map((log) => RobotLog.fromJson(log)).toList();
    } else {
      throw Exception('Failed to load logs');
    }
  }

  Future<Map<String, dynamic>> sendCommand(int robotId, String command) async {
    final response = await http.post(
      Uri.parse('$baseUrl/control/command'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'robot_id': robotId,
        'command': command,
      }),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      // Return error message or throw an exception
      return {'status': 'error', 'message': 'Failed to send command.'};
    }
  }

  Future<DeliveryRecord> createDelivery({
    required int robotId,
    required String message,
    required String address,
    required String inventoryIds,
    required String quantity,
    required String status,
    double? startX,
    double? startY,
    double? destX,
    double? destY,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/deliveryRecord/'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'robot_id': robotId,
        'message': message,
        'address': address,
        'inventory_ids': inventoryIds,
        'quantity': quantity,
        'status': status,
        'start_pos_x': startX,
        'start_pos_y': startY,
        'dest_pos_x': destX,
        'dest_pos_y': destY,
      }),
    );

    if (response.statusCode == 200) {
      return DeliveryRecord.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to create delivery record');
    }
  }
}

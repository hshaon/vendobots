import 'dart:convert';
import 'dart:math';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:untitled3/models/DeliveryRecord.dart';
import '../Enum/DeliveryRecordStatus.dart';
import '../models/products.dart';
import 'ControlCamera.dart';

class DeliveryRecordService {
  static String baseUrl = dotenv.env['BE_URL'] ?? '';
  static String idRobot = dotenv.env['ID_ROBOT'] ?? '';

  static Future<List<DeliveryRecord>> getAllRecordByRobotID() async {
    if (baseUrl.isEmpty) throw Exception('BE_URL not set');

    final response = await http.get(
      Uri.parse('$baseUrl/deliveryRecord/$idRobot'),
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(response.body);
      return data.map((json) => DeliveryRecord.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load DeliveryRecord');
    }
  }

  static String generate10DigitNumber() {
    Random random = Random();
    String number = '';

    for (int i = 0; i < 10; i++) {
      number += random.nextInt(10).toString(); // 0–9
    }
    return number;
  }

  static Future<String> handleFailCase() async {
    DateTime now = DateTime.now();

    DeliveryRecord record = DeliveryRecord(
      robotId: idRobot,
      address: '',
      status: DeliveryRecordStatus.FAILED.toString().split('.').last,

      message: "Transaction finish!",
      inventoryIds: "",
      quantity: "",
      videourl: generate10DigitNumber(),
      statisfied_level: "",
      createdAt: now,
      lastUpdatedAt: now,
      start_pos_x: 0.0,
      start_pos_y: 0.0,
      dest_pos_x: 0.0,
      dest_pos_y: 0.0,
    );

    try {
      //print(jsonEncode(record.toJson()));
      ControlCamera.callCameraAPI(action: 'stop', videourl: record.videourl);
      final response = await http.post(
        Uri.parse("$baseUrl/deliveryRecord/"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(record.toJson()), // serialize your DeliveryRecord
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        print("Delivery record sent successfully!");
        return record.videourl;
      } else {
        return "";
      }
    } catch (e) {
      return "";
    }
    return "";
  }
}

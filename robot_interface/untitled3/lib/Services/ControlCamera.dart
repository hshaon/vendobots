import 'dart:async';

import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;

class ControlCamera {
  static String robotId = dotenv.env['ID_ROBOT'] ?? "1";

   /*static Future<void> callCameraAPI({required String action, required String dateCreated}) async {
     final String apiUrl =
         'https://hricameratest.onrender.com/controlCamera/?IDRobot=$robotId&action=$action&dateCreated=$dateCreated';

     try {
       final response = await http.get(Uri.parse(apiUrl));
       if (response.statusCode == 200) {
         print('✅ API call successful: ${response.body}');
       } else {
         print(
             '⚠️ API call failed with status: ${response.statusCode}, body: ${response.body}');
       }
     } catch (e) {
       print('❌ API call error: $e');
     }
   }*/

   static Future<void> callCameraAPI({
     required String action,
     required String videourl,
   }) async {
     final String apiUrl =
         'https://hricameratest.onrender.com/controlCamera/?IDRobot=$robotId&action=$action&videourl=$videourl';
     // Fire-and-forget
     Future(() async {
       try {
         final response = await http.get(Uri.parse(apiUrl));
         if (response.statusCode == 200) {
           print('✅ API call successful: ${response.body}');
         } else {
           print('⚠️ API call failed: ${response.statusCode}, body: ${response.body}');
         }
       } catch (e) {
         print('❌ API call error: $e');
       }
     });
  }


  static void callCameraAPI2({
    required String action,
    required String videourl,
  }) {
    final apiUrl =
        'https://hricameratest.onrender.com/controlCamera/?IDRobot=$robotId&action=$action&videourl=$videourl';

    unawaited(
      http.get(Uri.parse(apiUrl)).then(
            (_) {},          // success (ignored)
        onError: (e) {    // error (swallowed)
          print('API error: $e');
        },
      ),
    );
  }



}

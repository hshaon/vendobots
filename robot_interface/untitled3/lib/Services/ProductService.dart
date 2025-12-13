import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';
import '../models/products.dart';

class ProductService {
  static String beUrl = dotenv.env['BE_URL'] ?? '';
  static String idRobot = dotenv.env['ID_ROBOT'] ?? '';

  static Future<List<Product>> fetchProducts() async {
    List<Product> loadProducts = []; // initialize it so it's always defined

    try {
      // Fetch robot data from API
      final response = await http.get(Uri.parse("$beUrl/robots/$idRobot"));

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);

        // Extract the inventory_items list
        loadProducts = (data['inventory_items'] as List)
            .map((e) => Product.fromJson(e))
            .toList();
      } else {
        print('Failed to load data from API: ${response.statusCode}');
      }
    } catch (e) {
      print('Error loading data: $e');
    }

    // return here, NOT in finally
    return loadProducts;
  }

}

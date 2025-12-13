import 'package:hive/hive.dart';

part 'products.g.dart';

@HiveType(typeId: 1)
class Product extends HiveObject {
  @HiveField(0)
  final int id;

  @HiveField(1)
  final String name;

  @HiveField(2)
  final String imagePath;

  @HiveField(3)
  double price;

  @HiveField(4)
  int quantity;

  @HiveField(5)
  String category;

  Product({
    required this.id,
    required this.name,
    required this.imagePath,
    required this.price,
    required this.quantity,
    required this.category,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'],
      name: json['name'],
      imagePath: json['image_url'] ?? "assets/images/cocacola.png",
      price: (json['price'] as num).toDouble(),
      quantity: json['quantity'],
      category: json['category'],
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'image_url': imagePath,
    'price': price,
    'quantity': quantity,
    'category': category,
  };
}

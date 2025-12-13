import 'products.dart';
import 'package:hive/hive.dart';

part 'cart.g.dart';

@HiveType(typeId: 0)
class CartItem extends HiveObject {
  @HiveField(0)
  String id;

  @HiveField(1)
  final Product product;

  @HiveField(2)
  int quantity;

  CartItem({required this.id, required this.product, this.quantity = 1});

  double get totalPrice => product.price * quantity;
}

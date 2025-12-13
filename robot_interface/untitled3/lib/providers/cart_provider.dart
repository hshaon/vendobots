import 'package:flutter/material.dart';
import 'package:hive/hive.dart';

import '../models/cart.dart';
import '../models/products.dart';

class CartProvider extends ChangeNotifier {
  final String _boxName = 'cartBox';
  List<CartItem> _items = [];

  List<CartItem> get items => _items;

  int get totalItems => _items.fold(0, (sum, item) => sum + item.quantity);

  double get totalPrice => _items.fold(0, (sum, item) => sum + item.totalPrice);

  /// Load dữ liệu từ Hive
  Future<void> loadCartFromHive() async {
    final box = await Hive.openBox<CartItem>(_boxName);
    _items = box.values.toList();
    notifyListeners();
  }

  Future<void> addToCart(Product product, {int quantity = 1}) async {
    final box = Hive.box<CartItem>(_boxName);

    final index = _items.indexWhere(
      (e) => e.product.name == product.name && e.product.id == product.id,
    );
    if (index != -1) {
      _items[index].quantity += quantity;
      await _items[index].save();
    } else {
      final newItem = CartItem(
        id: DateTime.now().toIso8601String(),
        product: product,
        quantity: quantity,
      );
      await box.add(newItem);
      _items.add(newItem);
    }
    notifyListeners();
  }

  Future<void> updateQuantity(
      Product product,
      int newQuantity,
      ) async {
    final box = Hive.box<CartItem>(_boxName);

    // Find the item in the cart
    final index = _items.indexWhere(
          (e) => e.product.name == product.name && e.product.id == product.id,
    );

    if (index != -1) {
      final item = _items[index];

      if (newQuantity > 0) {
        // Update quantity
        item.quantity = newQuantity;
        await item.save();
      } else {
        // If newQuantity is 0 or less, remove the item
        await item.delete();
        _items.removeAt(index);
      }

      notifyListeners();
    }
  }


  Future<void> removeFromCart(
    Product product, {
    bool isRemoveItem = false,
  }) async {
    final box = Hive.box<CartItem>(_boxName);
    final index = _items.indexWhere(
      (e) => e.product.name == product.name && e.product.id == product.id,
    );
    if (index != -1) {
      final item = _items[index];
      if (item.quantity > 1 && !isRemoveItem) {
        item.quantity--;
        await item.save();
      } else {
        await item.delete();
        _items.removeAt(index);
      }
      notifyListeners();
    }
  }

  void clearCart() {
    _items.clear();
    notifyListeners();
  }
}

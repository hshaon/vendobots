import 'package:flutter/material.dart';
import 'package:untitled3/models/products.dart';

class ProductCard extends StatefulWidget {
  final Product product;
  final Function(int) onAddToCart;

  const ProductCard({
    super.key,
    required this.product,
    required this.onAddToCart,
  });

  @override
  State<ProductCard> createState() => _ProductCardState();
}

class _ProductCardState extends State<ProductCard> {
  int quantity = 1;

  void _increaseQty() {
    setState(() {
      quantity++;
    });
  }

  void _decreaseQty() {
    if (quantity > 1) {
      setState(() {
        quantity--;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            Expanded(
              child: Image.network(widget.product.imagePath, fit: BoxFit.contain),
            ),
            const SizedBox(height: 8),
            Text(
              widget.product.name,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
            Text(
              "\$${widget.product.price.toStringAsFixed(2)}",
              style: const TextStyle(fontSize: 16, color: Colors.grey),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(30),
                    color: Colors.redAccent.withOpacity(0.08),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        onPressed: _decreaseQty,
                        icon: const Icon(Icons.remove_circle_outline),
                      ),
                      Text(
                        "$quantity",
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      IconButton(
                        onPressed: _increaseQty,
                        icon: const Icon(Icons.add_circle_outline),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                ElevatedButton(
                  onPressed: () => {
                    widget.onAddToCart(quantity),
                    setState(() {
                      quantity = 1;
                    }),
                  },
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.all(12),
                  ),
                  child: const Icon(Icons.add_shopping_cart),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

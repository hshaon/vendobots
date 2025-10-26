class InventoryItem {
  final int id;
  final String name;
  final String? imageUrl;
  final double? price;
  final int quantity;
  final int? robotId;

  InventoryItem({
    required this.id,
    required this.name,
    this.imageUrl,
    this.price,
    required this.quantity,
    this.robotId,
  });

  factory InventoryItem.fromJson(Map<String, dynamic> json) {
    return InventoryItem(
      id: json['id'],
      name: json['name'],
      imageUrl: json['image_url'],
      price: json['price'] != null ? (json['price'] as num).toDouble() : null,
      quantity: json['quantity'],
      robotId: json['robot_id'],
    );
  }
}
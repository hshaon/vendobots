import 'inventory_item.dart'; // We will create this next

class Robot {
  final int id;
  final String name;
  final String? imageUrl;
  final String status;
  final int batteryLevel;
  final DateTime lastUpdated;
  final List<InventoryItem> inventoryItems;

  final double currentPosX;
  final double currentPosY;

  Robot({
    required this.id,
    required this.name,
    this.imageUrl,
    required this.status,
    required this.batteryLevel,
    required this.lastUpdated,
    required this.inventoryItems,
    required this.currentPosX,
    required this.currentPosY,
  });

  factory Robot.fromJson(Map<String, dynamic> json) {
    var itemsList = json['inventory_items'] as List;
    List<InventoryItem> items =
        itemsList.map((i) => InventoryItem.fromJson(i)).toList();

    return Robot(
      id: json['id'],
      name: json['name'],
      imageUrl: json['image_url'],
      status: json['status'],
      batteryLevel: json['battery_level'],
      lastUpdated: DateTime.parse(json['last_updated']),
      inventoryItems: items,

      currentPosX: (json['current_pos_x'] as num?)?.toDouble() ?? 0.0,
      currentPosY: (json['current_pos_y'] as num?)?.toDouble() ?? 0.0,
    );
  }
}
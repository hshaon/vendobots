class DeliveryRecord {
  final int id;
  final String message;
  final int robotId;
  final String address;
  final String? videourl;
  final String inventoryIds;
  final String quantity;
  final String status;
  final DateTime createdAt;
  final DateTime lastUpdatedAt;
  final double? startPosX;
  final double? startPosY;
  final double? destPosX;
  final double? destPosY;

  DeliveryRecord({
    required this.id,
    required this.message,
    required this.robotId,
    required this.address,
    this.videourl,
    required this.inventoryIds,
    required this.quantity,
    required this.status,
    required this.createdAt,
    required this.lastUpdatedAt,
    this.startPosX,
    this.startPosY,
    this.destPosX,
    this.destPosY,
  });

  factory DeliveryRecord.fromJson(Map<String, dynamic> json) {
    return DeliveryRecord(
      id: json['id'],
      message: json['message'],
      robotId: json['robot_id'],
      address: json['address'],
      videourl: json['videourl'],
      inventoryIds: json['inventory_ids'],
      quantity: json['quantity'],
      status: json['status'],
      createdAt: DateTime.parse(json['created_at']),
      lastUpdatedAt: DateTime.parse(json['last_updated_at']),
      // Handle numeric values that could be int or double, and also null
      startPosX: (json['start_pos_x'] as num?)?.toDouble(),
      startPosY: (json['start_pos_y'] as num?)?.toDouble(),
      destPosX: (json['dest_pos_x'] as num?)?.toDouble(),
      destPosY: (json['dest_pos_y'] as num?)?.toDouble(),
    );
  }
}
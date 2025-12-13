import 'dart:ffi';

class DeliveryRecord {
  final String? id;
  final String robotId;
  final String address;
  final String status;
  final String message;
  final String inventoryIds;
  final String quantity;
  final String videourl;
  final String statisfied_level;
  final DateTime? createdAt;
  final DateTime? lastUpdatedAt;
  final double  start_pos_x;
  final double  start_pos_y;
  final double  dest_pos_x;
  final double  dest_pos_y;

  DeliveryRecord({
    this.id,
    required this.robotId,
    required this.address,
    required this.status,
    required this.message,
    required this.inventoryIds,
    required this.quantity,
    required this.videourl,
    required this.statisfied_level,
    required this.createdAt,
    required this.lastUpdatedAt,
    required this.start_pos_x,
    required this.start_pos_y,
    required this.dest_pos_x,
    required this.dest_pos_y,
  });

  // Convert from JSON (API response)
  factory DeliveryRecord.fromJson(Map<String, dynamic> json) {
    return DeliveryRecord(
      id: json['id'],
      robotId: json['robot_id'],
      address: json['address'],
      status: json['status'],
      message: json['message'],
      inventoryIds: json['inventory_ids'],
      quantity: json['quantity'],
      videourl: json['videourl'],
      statisfied_level:json['statisfied_level'],
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : null,
      lastUpdatedAt: json['last_updated_at'] != null
          ? DateTime.parse(json['last_updated_at'])
          : null,
      start_pos_x: json['start_pos_x'],
      start_pos_y: json['start_pos_y'],
      dest_pos_x: json['dest_pos_x'],
      dest_pos_y: json['dest_pos_y'],
    );
  }

  // Convert to JSON (for API requests)
  Map<String, dynamic> toJson() {
    print(inventoryIds);
    return {
      'id': id,
      'robot_id': robotId,
      'address': address,
      'status': status,
      'message': message,
      'inventory_ids': inventoryIds,
      'quantity': quantity,
      'videourl': videourl,
      'statisfied_level': statisfied_level,
      'created_at': createdAt?.toIso8601String(),
      'last_updated_at': lastUpdatedAt?.toIso8601String(),
      'start_pos_x': start_pos_x,
      'start_pos_y': start_pos_y,
      'dest_pos_x': dest_pos_x,
      'dest_pos_y': dest_pos_y,

    };
  }
}

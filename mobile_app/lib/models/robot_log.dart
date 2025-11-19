class RobotLog {
  final int id;
  final String message;
  final int robotId;
  final DateTime createdAt;

  RobotLog({
    required this.id,
    required this.message,
    required this.robotId,
    required this.createdAt,
  });

  factory RobotLog.fromJson(Map<String, dynamic> json) {
    return RobotLog(
      id: json['id'],
      message: json['message'],
      robotId: json['robot_id'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

import 'package:flutter/material.dart';
import '../models/robot.dart';
import '../models/robot_log.dart';
import '../services/api_service.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  // Futures for loading data from the API
  late Future<List<Robot>> futureRobots;
  late Future<List<RobotLog>> futureLogs;
  final ApiService apiService = ApiService();

  @override
  void initState() {
    super.initState();
    // Start fetching data when the page loads
    futureRobots = apiService.getRobots();
    futureLogs = apiService.getLogs();
  }

  // Helper to refresh data
  void _refreshData() {
    setState(() {
      futureRobots = apiService.getRobots();
      futureLogs = apiService.getLogs();
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Refreshing data...')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Robot>>(
      // This builder waits for the robot data
      future: futureRobots,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        } else if (snapshot.hasError) {
          return Center(child: Text("Error loading robot: ${snapshot.error}"));
        } else if (snapshot.hasData && snapshot.data!.isNotEmpty) {
          // --- Data is loaded ---
          final robot = snapshot.data!.first; // Get the first robot
          final status = robot.status;
          final batteryLevel = robot.batteryLevel / 100.0; // Convert 100 to 1.0

          Color statusColor = (status.toLowerCase() == "idle")
              ? Colors.amber
              : (status.toLowerCase() == "active" || status.toLowerCase() == "delivering"
                  ? Colors.green
                  : Colors.red);

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // --- Robot Image ---
                CircleAvatar(
                  radius: 60,
                  // Use network image if available, otherwise fallback
                  backgroundImage: (robot.imageUrl != null && robot.imageUrl!.isNotEmpty)
                      ? NetworkImage(robot.imageUrl!)
                      : const AssetImage('assets/robot.jpg') as ImageProvider,
                  onBackgroundImageError: (_, __) {},
                  backgroundColor: Colors.grey.shade300,
                  child: (robot.imageUrl == null || robot.imageUrl!.isEmpty)
                      ? const Icon(Icons.smart_toy, size: 60, color: Colors.white)
                      : null,
                ),
                const SizedBox(height: 16),

                // --- Robot Name + Status (from API) ---
                Text(
                  robot.name,
                  style: Theme.of(context).textTheme.headlineSmall!.copyWith(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.circle, color: statusColor, size: 12),
                    const SizedBox(width: 6),
                    Text("Status: $status",
                        style: TextStyle(fontSize: 16, color: statusColor, fontWeight: FontWeight.w600)),
                  ],
                ),
                const SizedBox(height: 20),

                // --- Battery and Connection Cards (from API) ---
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _infoCard(
                      icon: Icons.battery_full,
                      label: "Battery",
                      value: "${(batteryLevel * 100).round()}%",
                      barValue: batteryLevel,
                      barColor: Colors.green,
                    ),
                    _infoCard(
                      icon: Icons.wifi,
                      label: "Signal",
                      value: "85%", // Mock data (API doesn't have this yet)
                      barValue: 0.85,
                      barColor: Colors.blue,
                    ),
                  ],
                ),
                const SizedBox(height: 30),

                // --- Quick Control Buttons ---
                Text("Quick Controls",
                    style: Theme.of(context).textTheme.titleMedium!.copyWith(fontWeight: FontWeight.bold)),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  alignment: WrapAlignment.center,
                  children: [
                    _controlButton(Icons.play_arrow, "Start", Colors.green),
                    _controlButton(Icons.stop, "Stop", Colors.red),
                    _controlButton(Icons.home, "Dock", Colors.blue),
                    _controlButton(Icons.store, "Vendor Mode", Colors.orange),
                    _controlButton(Icons.warning, "E-Stop", Colors.purple),
                    // Use the refresh button to re-fetch API data
                    _controlButton(Icons.refresh, "Refresh", Colors.grey, onPressed: _refreshData),
                  ],
                ),
                const SizedBox(height: 30),

                // --- Activity Log Placeholder (from API) ---
                Text("Recent Activity",
                    style: Theme.of(context).textTheme.titleMedium!.copyWith(fontWeight: FontWeight.bold)),
                const SizedBox(height: 10),

                // --- This builder waits for the log data ---
                FutureBuilder<List<RobotLog>>(
                  future: futureLogs,
                  builder: (context, logSnapshot) {
                    if (logSnapshot.connectionState == ConnectionState.waiting) {
                      return const Center(child: CircularProgressIndicator());
                    } else if (logSnapshot.hasError) {
                      return Center(child: Text("Error: ${logSnapshot.error}"));
                    } else if (logSnapshot.hasData && logSnapshot.data!.isNotEmpty) {
                      final logs = logSnapshot.data!;
                      return ListView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: logs.length,
                        // Show most recent logs first
                        itemBuilder: (context, index) => _activityCard(logs.reversed.toList()[index].message),
                      );
                    } else {
                      return _activityCard("No logs found.");
                    }
                  },
                ),
              ],
            ),
          );
        } else {
          // This happens if API returns no robots
          return const Center(
            child: Text("No robots found. Make sure your database has at least one robot."),
          );
        }
      },
    );
  }

  // Helper widget for info cards (No change)
  Widget _infoCard({
    required IconData icon,
    required String label,
    required String value,
    required double barValue,
    required Color barColor,
  }) {
    return Container(
      width: 150,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(color: Colors.grey.withOpacity(0.3), blurRadius: 5, offset: const Offset(0, 3)),
        ],
      ),
      child: Column(
        children: [
          Icon(icon, color: barColor, size: 30),
          const SizedBox(height: 8),
          Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          LinearProgressIndicator(value: barValue, color: barColor, backgroundColor: Colors.grey[200]),
        ],
      ),
    );
  }

  // Helper widget for control buttons (Slight change to add custom onPressed)
  Widget _controlButton(IconData icon, String label, Color color, {VoidCallback? onPressed}) {
    return FilledButton.icon(
      onPressed: onPressed ?? () {
        // Default action
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$label command sent (Mock)')),
        );
      },
      icon: Icon(icon),
      label: Text(label),
      style: FilledButton.styleFrom(
        backgroundColor: color,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      ),
    );
  }

  // Helper widget for activity log (No change)
  Widget _activityCard(String text) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        leading: const Icon(Icons.bolt, color: Colors.amber),
        title: Text(text),
        dense: true,
      ),
    );
  }
}

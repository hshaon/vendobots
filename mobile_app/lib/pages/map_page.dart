import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/robot.dart';

class MapPage extends StatefulWidget {
  const MapPage({super.key});

  @override
  State<MapPage> createState() => _MapPageState();
}

class _MapPageState extends State<MapPage> {
  final ApiService _apiService = ApiService();
  final int _robotId = 1; // Assuming we are operating the primary robot
  Robot? _currentRobot;
  Offset? _destinationPoint; // Stores the map pixel coordinate of the destination

  // --- MAP CONSTANTS (Simulation for 10x10 meter map) ---
  final double _mapMeterWidth = 10.0;  // Assume map represents 10 meters wide/tall

  @override
  void initState() {
    super.initState();
    _fetchRobotData();
  }

  // --- API CALLS ---
  Future<void> _fetchRobotData() async {
    try {
      List<Robot> robots = await _apiService.getRobots(); 
      setState(() {
        _currentRobot = robots.firstWhere((r) => r.id == _robotId);
      });
    } catch (e) {
      print("Error fetching robot data: $e");
    }
  }

  Future<void> _sendWaypoint(double destX, double destY) async {
    // 1. Send the destination to the delivery records
    try {
      // Create a delivery record representing the user setting a goal
      await _apiService.createDeliveryRecord(
        robotId: _robotId, 
        message: "User set destination: (${destX.toStringAsFixed(2)}, ${destY.toStringAsFixed(2)})",
        address: "Map Destination", // Placeholder address
        status: "WAITING", 
        startX: _currentRobot?.xCoord, 
        startY: _currentRobot?.yCoord,
        destX: destX, 
        destY: destY
      );

      // 2. Simulate the robot immediately moving to the new location (for quick visualization)
      // NOTE: In a real system, you would send a ROS goal command here, and the robot's 
      // actual location would be updated by a background process.
      await _apiService.updateRobotLocation(
        robotId: _robotId, 
        xCoord: destX, 
        yCoord: destY
      );

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Goal set & simulated at X:${destX.toStringAsFixed(2)} Y:${destY.toStringAsFixed(2)} meters.')),
      );
      _fetchRobotData(); // Refresh the map to show the robot at the new goal
    } catch (e) {
      print("Error setting waypoint: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to set goal.')),
      );
    }
  }

  // --- COORDINATE HANDLING ---
  void _handleMapTap(TapDownDetails details, double mapWidth, double mapHeight) {
    if (_currentRobot == null) return;
    
    // 1. Store the raw pixel coordinates for visualization
    setState(() {
      _destinationPoint = details.localPosition;
    });

    // 2. Convert pixel coordinates to ROS Map coordinates (Meters)
    // Formula: (Pixel Position / Map Widget Dimension) * Real World Dimension (Meters)
    double meterX = (details.localPosition.dx / mapWidth) * _mapMeterWidth;
    double meterY = (details.localPosition.dy / mapHeight) * _mapMeterWidth; 

    // 3. Send the command
    _sendWaypoint(meterX, meterY);
  }

  Offset _meterToPixel(double mapWidth, double mapHeight) {
    if (_currentRobot == null) return const Offset(-100, -100);

    // Formula: (Meter Position / Real World Dimension (Meters)) * Map Widget Dimension
    double pixelX = (_currentRobot!.xCoord / _mapMeterWidth) * mapWidth;
    double pixelY = (_currentRobot!.yCoord / _mapMeterWidth) * mapHeight;

    // Ensure markers are centered on the widget's location
    return Offset(pixelX, pixelY);
  }

  // --- UI RENDERING ---
  @override
  Widget build(BuildContext context) {
    if (_currentRobot == null) {
        return const Center(child: CircularProgressIndicator());
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Interactive SLAM Map')),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final double containerWidth = constraints.maxWidth;
          final double containerHeight = constraints.maxHeight;

          return GestureDetector(
            onTapDown: (details) => _handleMapTap(details, containerWidth, containerHeight),
            child: Container(
              width: containerWidth,
              height: containerHeight,
              color: Colors.grey[200], 
              child: Stack(
                children: [
                  // 1. The Map Image
                  Image.asset(
                    'assets/images/map.png', // CRITICAL: Ensure this path is correct
                    width: containerWidth,
                    height: containerHeight,
                    fit: BoxFit.cover,
                    errorBuilder: (context, error, stackTrace) {
                      return const Center(child: Text("ERROR: Map Image (assets/images/map.png) Not Found", style: TextStyle(color: Colors.red)));
                    },
                  ),
                  
                  // 2. Robot Current Location Marker
                  Positioned(
                    left: _meterToPixel(containerWidth, containerHeight).dx - 10, // Offset by marker size
                    top: _meterToPixel(containerWidth, containerHeight).dy - 10,
                    child: const Tooltip(
                      message: "Robot Location (Current)",
                      child: CircleAvatar(
                        radius: 10,
                        backgroundColor: Colors.blue,
                        child: Icon(Icons.android, size: 12, color: Colors.white),
                      ),
                    ),
                  ),
                  
                  // 3. User Destination Marker
                  if (_destinationPoint != null)
                    Positioned(
                      left: _destinationPoint!.dx - 10, // Offset by marker size
                      top: _destinationPoint!.dy - 10,
                      child: const Tooltip(
                        message: "Destination Goal (Click to move)",
                        child: CircleAvatar(
                          radius: 10,
                          backgroundColor: Colors.red,
                          child: Icon(Icons.flag, size: 12, color: Colors.white),
                        ),
                      ),
                    ),

                  // 4. Status Overlay
                  Positioned(
                    bottom: 10,
                    left: 10,
                    child: Container(
                      padding: const EdgeInsets.all(5),
                      color: Colors.black54,
                      child: Text(
                        "Robot X:${_currentRobot!.xCoord.toStringAsFixed(2)}m, Y:${_currentRobot!.yCoord.toStringAsFixed(2)}m",
                        style: const TextStyle(color: Colors.white),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
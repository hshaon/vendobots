import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/robot.dart';

class MapPage extends StatefulWidget {
  final Robot? robot; // Pass in the robot
  final bool isPickerMode; // Are we picking a location or just viewing?

  const MapPage({
    super.key,
    this.robot,
    this.isPickerMode = false, // Default to false (view-only mode)
  });

  @override
  State<MapPage> createState() => _MapPageState();
}

class _MapPageState extends State<MapPage> {
  final ApiService apiService = ApiService();
  Robot? _robot; // Internal state for the robot
  Offset? destinationPixel; // Tapped destination in PIXELS
  Offset? robotPixel; // Robot position in PIXELS

  Timer? _robotPositionTimer;

  // --- COORDINATE TRANSFORM DATA ---
  // !! YOU MUST UPDATE THESE VALUES FROM YOUR SLAM MAP !!
  final double mapResolution = 0.05; // meters / pixel
  final double mapOriginX = -10.0; // meters
  final double mapOriginY = -10.0; // meters
  // ------------------------------------

  @override
  void initState() {
    super.initState();
    // If a robot was passed in, use it immediately.
    if (widget.robot != null) {
      _updateRobotData(widget.robot!);
    } else {
      // Otherwise, fetch the first robot (for view-only mode)
      _fetchRobotData();
    }

    // Only start the poller if we are in view-only mode
    if (!widget.isPickerMode) {
      _robotPositionTimer =
          Timer.periodic(const Duration(seconds: 2), (timer) {
        _fetchRobotData();
      });
    }
  }

  @override
  void dispose() {
    _robotPositionTimer?.cancel();
    super.dispose();
  }

  // Helper to set robot data and update its pixel position
  void _updateRobotData(Robot robot) {
    setState(() {
      _robot = robot;
      robotPixel = _mapToPixel(
        Offset(_robot!.currentPosX, _robot!.currentPosY),
      );
    });
  }

  // Helper to fetch the first robot from the API
  Future<void> _fetchRobotData() async {
    try {
      List<Robot> robots = await apiService.getRobots();
      if (robots.isNotEmpty && mounted) {
        _updateRobotData(robots.first);
      }
    } catch (e) {
      if (mounted) {
        print("Error fetching robot: $e");
      }
    }
  }

  // Convert logical MAP (meters) to image PIXEL
  Offset _mapToPixel(Offset mapCoords) {
    double pixelX = (mapCoords.dx - mapOriginX) / mapResolution;
    double pixelY = (mapCoords.dy - mapOriginY) / mapResolution;
    // Note: You may need to flip the Y-axis depending on map orientation
    // e.g., pixelY = (imageHeightInPixels - pixelY);
    return Offset(pixelX, pixelY);
  }

  // Convert image PIXEL to logical MAP (meters)
  Offset _pixelToMap(Offset pixelCoords) {
    double mapX = (pixelCoords.dx * mapResolution) + mapOriginX;
    double mapY = (pixelCoords.dy * mapResolution) + mapOriginY;
    return Offset(mapX, mapY);
  }

  // Store the tapped pixel location
  void _handleMapTap(TapDownDetails details) {
    setState(() {
      destinationPixel = details.localPosition;
    });
  }

  // This function is now multipurpose
  void _confirmDestination() {
    if (destinationPixel == null) return;

    // Convert PIXEL destination to MAP coordinates
    Offset destinationMap = _pixelToMap(destinationPixel!);

    if (widget.isPickerMode) {
      // If we are in "picker mode", pop the screen and
      // return the selected logical (map) coordinates.
      Navigator.pop(context, destinationMap);
    } else {
      // If we are in "view mode" (not picking),
      // we would create a delivery record.
      // For now, just show a snackbar.
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text(
                'View-only location: (${destinationMap.dx.toStringAsFixed(2)}, ${destinationMap.dy.toStringAsFixed(2)})')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    // Add a Scaffold to get an AppBar
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.isPickerMode ? 'Select Location' : 'Robot Map'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: Colors.black87,
      ),
      // Make the app bar float over the map
      extendBodyBehindAppBar: true,
      body: InteractiveViewer(
        boundaryMargin: const EdgeInsets.all(20.0),
        minScale: 0.1,
        maxScale: 4.0,
        child: Stack(
          children: [
            // --- 1. The Map Image ---
            GestureDetector(
              onTapDown: _handleMapTap,
              child: Image.asset(
                'assets/images/map.png',
                fit: BoxFit.cover,
                width: double.infinity,
                height: double.infinity,
              ),
            ),

            // --- 2. The Robot Marker ---
            if (robotPixel != null)
              Positioned(
                left: robotPixel!.dx - 12, // Center the 24x24 circle
                top: robotPixel!.dy - 12,
                child: Tooltip(
                  message: "Robot ${_robot?.name}",
                  child: Container(
                    width: 24,
                    height: 24,
                    decoration: BoxDecoration(
                      color: Colors.blue.withOpacity(0.8),
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 2),
                    ),
                  ),
                ),
              ),

            // --- 3. The Destination Marker ---
            if (destinationPixel != null)
              Positioned(
                left: destinationPixel!.dx - 12, // Center the 24x24 circle
                top: destinationPixel!.dy - 12,
                child: Tooltip(
                  message: "Destination",
                  child: Container(
                    width: 24,
                    height: 24,
                    decoration: BoxDecoration(
                      color: Colors.red.withOpacity(0.8),
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 2),
                    ),
                  ),
                ),
              ),

            // --- 4. The Confirmation Button ---
            // This button will pan/zoom with the map.
            if (destinationPixel != null)
              Positioned(
                bottom: 20,
                left: 20,
                right: 20,
                child: ElevatedButton(
                  onPressed: _confirmDestination,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: Text(
                    // Change button text based on mode
                    widget.isPickerMode
                        ? 'Select This Location'
                        : 'Confirm Destination',
                    style: const TextStyle(color: Colors.white, fontSize: 16),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
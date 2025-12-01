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
  final double mapResolution = 0.05; // meters / pixel
  final double mapOriginX = -17; // meters
  final double mapOriginY = -29.7; // meters
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

  // --- 1. Robot Coordinates (Meters) -> Screen (Pixels) ---
  Offset _mapToPixel(Offset mapCoords) {
    double pixelX = (mapCoords.dx - mapOriginX) / mapResolution;

    // FIX: Invert the Y input. 
    // Since 'Up' is positive for the robot but 'Down' is positive for pixels,
    // we flip the sign of the incoming Y coordinate.
    double pixelY = (-mapCoords.dy - mapOriginY) / mapResolution;
    
    return Offset(pixelX, pixelY);
  }

  // --- 2. Screen (Pixels) -> Robot Coordinates (Meters) ---
  Offset _pixelToMap(Offset pixelCoords) {
    double mapX = (pixelCoords.dx * mapResolution) + mapOriginX;
    
    // FIX: Invert the Y result.
    // Calculate the raw value, then flip the sign so "Up" becomes positive.
    double rawY = (pixelCoords.dy * mapResolution) + mapOriginY;
    double mapY = -rawY;

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
    return Scaffold(
      // 1. Darker background makes the map pop
      backgroundColor: Colors.grey[900], 
      appBar: AppBar(
        title: Text(
          widget.isPickerMode ? 'Select Location' : 'Robot Map',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.white.withOpacity(0.9),
        elevation: 0,
        foregroundColor: Colors.black87,
        centerTitle: true,
      ),
      extendBodyBehindAppBar: true,
      
      // 2. Constrained true ensures we start nicely fitted to the screen
      body: InteractiveViewer(
        boundaryMargin: const EdgeInsets.all(100.0), // Allow panning a bit past edges
        minScale: 0.1,
        maxScale: 5.0,
        constrained: true, // <--- CHANGE THIS BACK TO TRUE
        child: Center(
          child: FittedBox(
            fit: BoxFit.contain, // <--- Auto-scales map to fit screen width/height
            child: Container(
              // 3. Add a nice shadow to separate map from background
              decoration: BoxDecoration(
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.5),
                    blurRadius: 20,
                    spreadRadius: 5,
                  ),
                ],
              ),
              // This SizedBox ensures the Stack knows the exact size of your map image
              // You might need to adjust these values to match your 'map.png' resolution exactly
              // or remove SizedBox if Image.asset handles intrinsic size correctly.
              child: Stack(
                children: [
                  GestureDetector(
                    onTapDown: _handleMapTap,
                    child: Image.asset(
                      'assets/images/map.png',
                      // Remove fit: BoxFit.cover, allow natural size inside FittedBox
                    ),
                  ),

                  // --- Markers (unchanged) ---
                  if (robotPixel != null)
                    Positioned(
                      left: robotPixel!.dx - 12, 
                      top: robotPixel!.dy - 12,
                      child: _buildMarker(Colors.blue, "Robot"),
                    ),

                  if (destinationPixel != null)
                    Positioned(
                      left: destinationPixel!.dx - 12, 
                      top: destinationPixel!.dy - 12,
                      child: _buildMarker(Colors.red, "Dest"),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
      
      // Floating Action Button for confirmation (looks cleaner than a Positioned button)
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      floatingActionButton: destinationPixel != null
          ? FloatingActionButton.extended(
              onPressed: _confirmDestination,
              backgroundColor: Colors.green,
              icon: const Icon(Icons.check_circle),
              label: Text(widget.isPickerMode
                  ? 'Select Location'
                  : 'Confirm Destination'),
            )
          : null,
    );
  }

  // Helper widget to make markers look nicer
  Widget _buildMarker(Color color, String label) {
    return Tooltip(
      message: label,
      child: Container(
        width: 24,
        height: 24,
        decoration: BoxDecoration(
          color: color.withOpacity(0.9),
          shape: BoxShape.circle,
          border: Border.all(color: Colors.white, width: 2),
          boxShadow: [
            const BoxShadow(
              color: Colors.black26,
              blurRadius: 4,
              offset: Offset(0, 2),
            )
          ],
        ),
        child: Center(
          child: Container(
            width: 8,
            height: 8,
            decoration: const BoxDecoration(
              color: Colors.white,
              shape: BoxShape.circle,
            ),
          ),
        ),
      ),
    );
  }
}
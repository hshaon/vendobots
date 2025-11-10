// hshaon/vendobots/vendobots-Andrew/mobile_app/lib/pages/map_page.dart
import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/robot.dart';

class MapPage extends StatefulWidget {
  const MapPage({super.key});

  @override
  State<MapPage> createState() => _MapPageState();
}

class _MapPageState extends State<MapPage> {
  final ApiService apiService = ApiService(); // Or get from a provider
  Robot? robot; // We'll track one robot for this example
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
    _fetchRobotData();
    // Poll for robot position every 2 seconds
    _robotPositionTimer = Timer.periodic(const Duration(seconds: 2), (timer) {
      _fetchRobotData();
    });
  }

  @override
  void dispose() {
    _robotPositionTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchRobotData() async {
    try {
      // For this example, just get the first robot
      List<Robot> robots = await apiService.getRobots();
      if (robots.isNotEmpty) {
        setState(() {
          robot = robots.first;
          // Convert robot's MAP coordinates to PIXEL coordinates
          robotPixel = _mapToPixel(
            Offset(robot!.currentPosX, robot!.currentPosY),
          );
        });
      }
    } catch (e) {
      print("Error fetching robot: $e");
    }
  }

  // Convert logical MAP (meters) to image PIXEL
  Offset _mapToPixel(Offset mapCoords) {
    double pixelX = (mapCoords.dx - mapOriginX) / mapResolution;
    double pixelY = (mapCoords.dy - mapOriginY) / mapResolution;
    // Note: You may need to flip the Y-axis depending on map orientation
    // e.g., pixelY = (mapHeight - pixelY);
    return Offset(pixelX, pixelY);
  }

  // Convert image PIXEL to logical MAP (meters)
  Offset _pixelToMap(Offset pixelCoords) {
    double mapX = (pixelCoords.dx * mapResolution) + mapOriginX;
    double mapY = (pixelCoords.dy * mapResolution) + mapOriginY;
    return Offset(mapX, mapY);
  }

  void _handleMapTap(TapDownDetails details) {
    setState(() {
      // Store the destination as a PIXEL offset
      destinationPixel = details.localPosition;
    });

    // You can show a confirmation dialog here
    // "Send robot to this location?"
  }

  void _confirmDestination() {
    if (destinationPixel == null || robot == null) return;

    // Convert PIXEL destination to MAP coordinates
    Offset destinationMap = _pixelToMap(destinationPixel!);
    Offset startMap = _pixelToMap(robotPixel!);

    // Show a snackbar or loading indicator
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Sending robot to (${destinationMap.dx.toStringAsFixed(2)}, ${destinationMap.dy.toStringAsFixed(2)})')),
    );

    // Call the API to create the new delivery record
    apiService.createDelivery(
      robotId: robot!.id,
      message: "New delivery from map",
      address: "Map coordinates",
      inventoryIds: "[]", // Or get from a selection
      quantity: "[]",
      status: "WAITING",
      startX: startMap.dx,
      startY: startMap.dy,
      destX: destinationMap.dx,
      destY: destinationMap.dy,
    ).then((_) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Delivery task created!'), backgroundColor: Colors.green),
      );
      setState(() {
        destinationPixel = null; // Clear tap
      });
    }).catchError((e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
      );
    });
  }

@override
  Widget build(BuildContext context) {
    // --- ADD THIS WIDGET ---
    return InteractiveViewer(
      boundaryMargin: const EdgeInsets.all(20.0), // Optional: adds padding
      minScale: 0.1, // Optional: set min zoom
      maxScale: 4.0, // Optional: set max zoom
      // The child is your existing Stack
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
              left: robotPixel!.dx - 12, 
              top: robotPixel!.dy - 12,
              child: Tooltip(
                message: "Robot ${robot?.name}",
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
              left: destinationPixel!.dx - 12, 
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
          // This button will NOT move with the map, which is what we want.
          // To make it move with the map, put it inside the Stack.
          // To keep it static, leave it outside the InteractiveViewer
          // (which would require a different widget structure, like a Column).
          
          // For now, this button is inside the Stack, so it WILL pan/zoom.
          if (destinationPixel != null)
            Positioned(
              bottom: 20,
              left: 20,
              right: 20,
              child: ElevatedButton(
                onPressed: _confirmDestination,
                style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                child: const Text('Confirm Destination', style: TextStyle(color: Colors.white)),
              ),
            ),
        ],
      ),
    );
  }
}
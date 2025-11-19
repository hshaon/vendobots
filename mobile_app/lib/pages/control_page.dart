import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'package:flutter_mjpeg/flutter_mjpeg.dart';

class ControlPage extends StatefulWidget {
  const ControlPage({super.key});

  @override
  State<ControlPage> createState() => _ControlPageState();
}

class _ControlPageState extends State<ControlPage> {
  String _currentStatus = "Robot Ready";
  final ApiService _apiService = ApiService();
  final int _robotId = 1; 

  Future<void> _sendCommand(String command) async {
    setState(() {
      _currentStatus = "Sending command: ${command.toUpperCase()}...";
    });

    try {
      final result = await _apiService.sendCommand(_robotId, command);
      
      if (result['status'] == 'success') {
        setState(() {
          _currentStatus = result['message'];
        });
      } else {
        setState(() {
          _currentStatus = "ERROR: ${result['message']}";
        });
      }
    } catch (e) {
      setState(() {
        _currentStatus = "Connection Error: $e";
      });
    }
  }

  Widget _buildControlPad() {
    return Column(
      children: [
        // FORWARD Button
        ElevatedButton(
          onPressed: () => _sendCommand('forward'),
          child: const Icon(Icons.arrow_upward, size: 40),
        ),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // LEFT Button
            ElevatedButton(
              onPressed: () => _sendCommand('left'),
              child: const Icon(Icons.arrow_back, size: 40),
            ),
            // STOP Button
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24.0),
              child: ElevatedButton(
                onPressed: () => _sendCommand('stop'),
                style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                child: const Icon(Icons.stop, size: 40),
              ),
            ),
            // RIGHT Button
            ElevatedButton(
              onPressed: () => _sendCommand('right'),
              child: const Icon(Icons.arrow_forward, size: 40),
            ),
          ],
        ),
        // BACKWARD Button
        ElevatedButton(
          onPressed: () => _sendCommand('backward'),
          child: const Icon(Icons.arrow_downward, size: 40),
        ),
      ],
    );
  }

@override
  Widget build(BuildContext context) {
    // 1. Construct the Video Stream URL
    // This correctly resolves to something like http://127.0.0.1:8000/control/video_feed
    final String videoUrl = '${_apiService.baseUrl}/control/video_feed';

    return Scaffold(
      body: Stack(
        children: [
          // 1. Main Camera View (Image.network for MJPEG Stream)
          Center(
            child: SizedBox.expand(
              child: Image.network(
                videoUrl,
                fit: BoxFit.cover, 
                // Handles loading state
                loadingBuilder: (context, child, loadingProgress) {
                  if (loadingProgress == null) return child;
                  return const Center(
                    child: CircularProgressIndicator(color: Colors.white),
                  );
                },
                // Handles error state (e.g., if camera isn't running)
                errorBuilder: (context, error, stackTrace) {
                  return Container(
                    color: Colors.black,
                    child: const Center(
                      child: Text(
                        "ERROR: Could not connect to camera feed. Is FastAPI running and are you on the Control tab?",
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.redAccent, fontSize: 16),
                      ),
                    ),
                  );
                },
              ),
            ),
          ),

          // 2. Placeholder Mini-Map (Top Right)
          Positioned(
            top: 20,
            right: 20,
            child: Container(
              width: 120,
              height: 120,
              color: Colors.grey.withOpacity(0.8),
              alignment: Alignment.center,
              child: const Text(
                "MINI MAP",
                style: TextStyle(color: Colors.black54, fontSize: 12),
              ),
            ),
          ),

          // 3. Controls and Logs (Bottom Section)
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.9),
                boxShadow: const [BoxShadow(blurRadius: 10, color: Colors.black12)],
              ),
              child: Column(
                children: [
                  Text(
                    "STATUS: $_currentStatus",
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 16),
                  _buildControlPad(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
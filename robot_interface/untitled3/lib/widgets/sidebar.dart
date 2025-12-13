import 'dart:async';
import 'package:socket_io_client/socket_io_client.dart' as IO;

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:untitled3/enum/InteractionType.dart';

import '../Screens/order_screen.dart';
import '../Services/ControlCamera.dart';
import '../Services/LogService.dart';

class SideBar extends StatefulWidget {
  final bool isVisible;
  final VoidCallback onToggle;
  final InteractionType interactionType;

  const SideBar({
    super.key,
    required this.isVisible,
    required this.onToggle,
    required this.interactionType,
  });

  @override
  _SideBarState createState() => _SideBarState();
}

class _SideBarState extends State<SideBar> {
  int? selectedButtonIndex;
  Timer? _autoCloseTimer;
  late IO.Socket socket;

  @override
  void initState() {
    super.initState();
    _loadSelectedInteraction();
  }

  Future<void> _loadSelectedInteraction() async {
    final prefs = await SharedPreferences.getInstance();
    String? savedInteraction = prefs.getString('interactionType');

    setState(() {
      if (savedInteraction != null) {
        if (savedInteraction.contains('TOUCHSCREEN')) {
          selectedButtonIndex = 1;
        } else if (savedInteraction.contains('VOICE')) {
          selectedButtonIndex = 1;
        } else {
          // fallback to widget.interactionType if saved value is invalid
          selectedButtonIndex =
              (widget.interactionType == InteractionType.TOUCHSCREEN) ? 0 : 1;
        }
      } else {
        // no saved value, use widget.interactionType
        selectedButtonIndex =
            (widget.interactionType == InteractionType.TOUCHSCREEN) ? 0 : 1;
      }
    });
  }

  // @override
  // void didUpdateWidget(covariant SideBar oldWidget) {
  //   super.didUpdateWidget(oldWidget);
  //
  //   // If sidebar was just opened
  //   if (!oldWidget.isVisible && widget.isVisible) {
  //     _startAutoCloseTimer();
  //   }
  //
  //   // If sidebar was just closed manually, cancel the timer
  //   if (oldWidget.isVisible && !widget.isVisible) {
  //     _cancelAutoCloseTimer();
  //   }
  // }

  void _startAutoCloseTimer() {
    _autoCloseTimer?.cancel(); // cancel any existing timer
    _autoCloseTimer = Timer(const Duration(seconds: 100), () {
      // Close the sidebar after 10 seconds
      widget.onToggle();
    });
  }

  void _cancelAutoCloseTimer() {
    _autoCloseTimer?.cancel();
    _autoCloseTimer = null;
  }

  @override
  void dispose() {
    _cancelAutoCloseTimer(); // clean up
    super.dispose();
  }

  void _onButtonPressed(int index) async {
    setState(() {
      selectedButtonIndex = index;
    });

    final prefs = await SharedPreferences.getInstance();
    if (index == 0) {
      await prefs.setString(
        'interactionType',
        InteractionType.TOUCHSCREEN.toString(),
      );
    } else {
      await prefs.setString(
        'interactionType',
        InteractionType.VOICE.toString(),
      );
    }

    LogService.postLogService("Starting Record");
    socket.off('TourchScreenAction');
    socket.off('connect');
    socket.off('disconnect');
    socket.off('connect_error');
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const OrderScreen(typeProduct: 0)),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Do NOT set selectedButtonIndex here! It's managed by state & async load.

    return AnimatedContainer(
      duration: const Duration(milliseconds: 50),
      width: widget.isVisible ? 200 : 50,
      decoration: BoxDecoration(
        color: Colors.grey.shade900.withOpacity(0.95),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.4),
            offset: const Offset(2, 0),
            blurRadius: 6,
          ),
        ],
      ),
      child: Row(
        children: [
          if (widget.isVisible)
            Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Padding(
                    padding: const EdgeInsets.only(left: 20),
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: selectedButtonIndex == 0
                            ? Colors.blue
                            : Colors.white,
                      ),
                      onPressed: () => _onButtonPressed(1),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Image.asset(
                            'assets/images/touchIcon.png',
                            width: 70,
                            height: 70,
                          ),
                          const SizedBox(width: 8),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  Padding(
                    padding: const EdgeInsets.only(left: 20),
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: selectedButtonIndex == 1
                            ? Colors.blue
                            : Colors.white,
                      ),
                      onPressed: () => _onButtonPressed(1),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Image.asset(
                            'assets/images/voiceIcon.png',
                            width: 70,
                            height: 70,
                          ),
                          const SizedBox(width: 8),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),

          // Toggle button
          Container(
            width: 40,
            alignment: Alignment.center,
            child: IconButton(
              iconSize: 50,
              icon: Icon(
                widget.isVisible ? Icons.chevron_left : Icons.chevron_right,
              ),
              color: Colors.white,
              onPressed: () {
                if (widget.isVisible) {
                  _cancelAutoCloseTimer();
                }
                widget.onToggle();
              },
            ),
          ),
        ],
      ),
    );
  }
}

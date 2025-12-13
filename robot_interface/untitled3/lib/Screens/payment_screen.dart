import 'dart:async';
import 'dart:convert';
import 'dart:ffi';
import 'dart:math';
import 'dart:ui' as ui;

import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:socket_io_client/socket_io_client.dart' as IO;

import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:provider/provider.dart';
import 'package:untitled3/Enum/DeliveryRecordStatus.dart';
import 'package:untitled3/Enum/PAYMENTACTIONTYPE.dart';
import 'package:untitled3/Services/DeliveryRecordService.dart';

import '../Enum/AllActionInProject.dart';
import '../Enum/AllScreenInProject.dart';
import '../Services/ControlCamera.dart';
import '../Services/LogService.dart';
import '../Services/ProductService.dart';
import '../models/DeliveryRecord.dart';
import '../models/cart.dart';
import '../models/products.dart';
import '../providers/cart_provider.dart';
import 'cart_screen.dart';
import 'grid_screen.dart';
import 'order_screen.dart';

class PaymentScreen extends StatefulWidget {
  const PaymentScreen({super.key});

  @override
  State<PaymentScreen> createState() => _PaymentScreenState();
}

class _PaymentScreenState extends State<PaymentScreen> {
  final List<String> summaryOptions = [
    'Here!',
    'Location 1',
    'Location 2',
    'Location 3',
  ];

  late int reachTime = 60;
  final beUrl = dotenv.env['BE_URL'] ?? "http://10.0.2.2:8000/";
  final robotId = dotenv.env['ID_ROBOT'] ?? "1";

  String selectedSummary = 'Here!';

  late String x = "1";
  late String y = "1";

  final ScrollController _scrollController = ScrollController();
  Offset? _markerPos;
  double? _imageX, _imageY;

  bool _showScrollButton = true;
  late IO.Socket socket;
  late int isSuccess = 0;
  Timer? _inactivityTimer;

  String generate10DigitNumber() {
    Random random = Random();
    String number = '';

    for (int i = 0; i < 10; i++) {
      number += random.nextInt(10).toString(); // 0–9
    }
    return number;
  }

  void _startInactivityTimer() {
    _inactivityTimer?.cancel();

    _inactivityTimer = Timer(Duration(seconds: reachTime), () async {
      if (!mounted) return;

      // Show a blocking loading dialog
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) {
          return WillPopScope(
            onWillPop: () async => false, // disable back button
            child: AlertDialog(
              backgroundColor: Colors.white,
              title: Text(
                isSuccess == 0 ? "System Restarting" : "Booking Confirmed",
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    isSuccess == 0
                        ? "Please wait a moment, the system is restarting..."
                        : 'Thank you for your booking, products will transfer to your address soon\n Could you please make a survey bellow?',
                    style: TextStyle(fontSize: 16),
                    textAlign: TextAlign.center,
                  ),

                  const SizedBox(height: 20),

                  // ✅ Show image only when isSuccess == 1
                  if (isSuccess == 1)
                    Image.asset(
                      "assets/images/QRCODE.png",
                      width: 120,
                      height: 120,
                      fit: BoxFit.contain,
                    ),

                  // (Optional) add space or loader
                  if (isSuccess == 1) const SizedBox(height: 20),
                ],
              ),
            ),
          );
        },
      );
      if (isSuccess != 1) {
        String v_url = await DeliveryRecordService.handleFailCase();
      }
      //await ControlCamera.callCameraAPI(action: 'stop', videourl: v_url);
      LogService.postLogService(
        "Canceled transaction and stop record by camera!",
      );
      // ✅ Give UI time to render the dialog first
      // await Future.delayed(const Duration(milliseconds: 300));
      await Future.delayed(const Duration(seconds: 10));

      if (mounted) {
        final cartProvider = Provider.of<CartProvider>(context, listen: false);
        cartProvider.clearCart();
        Navigator.of(
          context,
        ).pushReplacement(MaterialPageRoute(builder: (_) => const GridPage()));
      }
    });
  }

  void _resetTimer() {
    _startInactivityTimer();
  }

  void _initSocket() {
    socket = IO.io(
      'https://hricameratest.onrender.com',
      IO.OptionBuilder()
          .setTransports(['websocket'])
          .enableReconnection()
          .disableAutoConnect()
          .build(),
    );

    socket.onConnect((_) {
      print('✅ Connected to server');
      socket.emit('join', {'room': robotId});
    });

    final cartProvider = Provider.of<CartProvider>(context, listen: false);
    socket.on('TourchScreenAction', (data) async {
      // print('Received action: $data');
      if (data['action'] ==
          PaymentActionType.CHANGEADDRESS.toString().split('.').last) {
        if (summaryOptions.contains(data['room'])) {
          setState(() {
            selectedSummary = data['room'];
          });
          print('Found!');
        } else {
          print('Not found!');
        }
      } else if (data['action'] ==
          PaymentActionType.DECISION.toString().split('.').last) {
        if (data['value'] == "ACCEPT") {
          await _handleConfirmRequest(cartProvider);
        }
        // socket.off('TourchScreenAction');
        // socket.off('connect');
        // socket.off('disconnect');
        // socket.off('connect_error');
        await _handleConfirmRequest(cartProvider);
        setState(() {
          reachTime = 0;
          isSuccess = 1;
        });
        _inactivityTimer?.cancel();
        _startInactivityTimer();
        // Show a blocking loading dialog
        // showDialog(
        //   context: context,
        //   barrierDismissible: false,
        //   builder: (context) {
        //     return WillPopScope(
        //       onWillPop: () async => false, // disable back button
        //       child: const AlertDialog(
        //         backgroundColor: Colors.white,
        //         title: Text(
        //           "Completed!",
        //           style: TextStyle(fontWeight: FontWeight.bold),
        //         ),
        //         content: Column(
        //           mainAxisSize: MainAxisSize.min,
        //           children: [
        //             Text(
        //               "Please wait a moment, the system is restarting...",
        //               style: TextStyle(fontSize: 16),
        //               textAlign: TextAlign.center,
        //             ),
        //             // SizedBox(height: 20),
        //             // CircularProgressIndicator(),
        //           ],
        //         ),
        //       ),
        //     );
        //   },
        // );
        // cartProvider.clearCart();
        // _inactivityTimer?.cancel();
        // LogService.postLogService("Transaction Finish(Accepted)!");
        // await Future.delayed(const Duration(milliseconds: 100));
        // Navigator.of(
        //   context,
        // ).pushReplacement(MaterialPageRoute(builder: (_) => GridPage()));
      } else if (data['action'] ==
          AllActionInproject.MOVE.toString().split('.').last) {
        if (data['Move2Page'] ==
            AllScreenInProject.ORDERSCREEN.toString().split('.').last) {
          if (mounted) {
            final int typeProduct = data['value'] != null ? data['value'] : 0;
            socket.off('TourchScreenAction');
            socket.off('connect');
            socket.off('disconnect');
            socket.off('connect_error');
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(
                builder: (_) => OrderScreen(typeProduct: typeProduct),
              ),
            );
          }
        // } else if (data['Move2Page'] ==
        //     AllScreenInProject.HOMEPAGESCREEN.toString().split('.').last) {
        //   if (mounted) {
        //     socket.off('TourchScreenAction');
        //     socket.off('connect');
        //     socket.off('disconnect');
        //     socket.off('connect_error');
        //     ControlCamera.callCameraAPI(action: 'stop', videourl: "None");
        //     LogService.postLogService("Staying in FirstScreen");
        //     Navigator.of(context).pushReplacement(
        //       MaterialPageRoute(builder: (_) => const GridPage()),
        //     );
        //   }
        } else if (data['Move2Page'] ==
            AllScreenInProject.CARTSCREEN.toString().split('.').last) {
          if (mounted) {
            socket.off('TourchScreenAction');
            socket.off('connect');
            socket.off('disconnect');
            socket.off('connect_error');
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (_) => const CartScreen()),
            );
          }
        }
      }
    });

    socket.onConnectError((err) => print('⚠️ Connect error: $err'));
    socket.onDisconnect((_) => print('❌ Disconnected'));

    socket.connect();
  }

  @override
  void initState() {
    super.initState();
    _startInactivityTimer();
    _initSocket();
    LogService.postLogService("Staying in PaymentScreen");
    _scrollController.addListener(() {
      if (_scrollController.position.pixels >=
          _scrollController.position.maxScrollExtent - 50) {
        if (_showScrollButton) {
          setState(() => _showScrollButton = false);
        }
      } else {
        if (!_showScrollButton) {
          setState(() => _showScrollButton = true);
        }
      }
    });
  }

  void _scrollToBottom() {
    _scrollController.animateTo(
      _scrollController.position.maxScrollExtent,
      duration: const Duration(milliseconds: 500),
      curve: Curves.easeOut,
    );
  }

  @override
  void dispose() {
    _inactivityTimer?.cancel();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _handleConfirmRequest(CartProvider cartProvider) async {
    if (cartProvider.items.isEmpty) return;
    List<String> inventoryIds = [];
    List<String> quantity = [];

    for (CartItem item in cartProvider.items) {
      inventoryIds.add(item.product.id.toString());
      quantity.add(item.quantity.toString());
    }

    DateTime now = DateTime.now();

    DeliveryRecord record = DeliveryRecord(
      robotId: robotId.toString(),
      address: "",
      status: this.x == "1"
          ? DeliveryRecordStatus.DELIVERIED.toString().split('.').last
          : DeliveryRecordStatus.NEW.toString().split('.').last,
      message: "Created successful!",
      inventoryIds: inventoryIds.join(', '),
      quantity: quantity.join(', '),
      videourl: generate10DigitNumber(),
      statisfied_level: "",
      createdAt: now,
      lastUpdatedAt: now,
      start_pos_x: 0.0,
      start_pos_y: 0.0,
      dest_pos_x: double.parse(this.x),
      dest_pos_y: double.parse(this.y),
    );

    print(record.toJson());
    try {
      //print(jsonEncode(record.toJson()));
      final response = await http.post(
        Uri.parse("$beUrl/deliveryRecord/"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(record.toJson()), // serialize your DeliveryRecord
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        print("Delivery record sent successfully!");
      } else {
        print("Failed to send delivery record: ${response.statusCode}");
        if (mounted) {
          socket.off('TourchScreenAction');
          socket.off('connect');
          socket.off('disconnect');
          socket.off('connect_error');
          LogService.postLogService(
            "Creating transaction fail and stop record by camera!",
          );
          _inactivityTimer?.cancel();
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(builder: (_) => const GridPage()),
          );
        }
      }
    } catch (e) {
      print("Error sending delivery record: $e");
      if (mounted) {
        socket.off('TourchScreenAction');
        socket.off('connect');
        socket.off('disconnect');
        socket.off('connect_error');
        LogService.postLogService(
          "Creating transaction fail and stop record by camera!",
        );
        _inactivityTimer?.cancel();
        Navigator.of(
          context,
        ).pushReplacement(MaterialPageRoute(builder: (_) => const GridPage()));
      }
    }

    ControlCamera.callCameraAPI(action: 'stop', videourl: record.videourl);
    LogService.postLogService(
      "Creating transaction successful and stop record by camera!",
    );
    cartProvider.clearCart();
  }

  @override
  Widget build(BuildContext context) {
    final cartProvider = Provider.of<CartProvider>(context);

    return GestureDetector(
      behavior: HitTestBehavior.translucent,
      onTap: _resetTimer,
      onPanDown: (_) => _resetTimer(),
      child: Scaffold(
        appBar: AppBar(
          leadingWidth: 80, // make space for bigger button
          leading: Padding(
            padding: const EdgeInsets.only(left: 12.0),
            child: ElevatedButton.icon(
              onPressed: () {
                Navigator.of(context).pushReplacement(
                  MaterialPageRoute(builder: (_) => const CartScreen()),
                );
              },
              icon: const Icon(Icons.arrow_back, size: 28), // bigger icon
              label: const Text(
                "",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 12,
                ),
              ),
            ),
          ),
          title: const Text(
            'Choosing Delivery Address:',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 24),
          ),
          centerTitle: true,
        ),
        body: Stack(
          children: [
            LayoutBuilder(
              builder: (context, constraints) {
                return SingleChildScrollView(
                  controller: _scrollController,
                  padding: const EdgeInsets.only(
                    left: 16,
                    right: 16,
                    top: 16,
                    bottom: 0,
                  ),
                  child: ConstrainedBox(
                    constraints: BoxConstraints(
                      minHeight: 500, // fill at least the screen
                    ),
                    child: IntrinsicHeight(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // your confirm button
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton(
                              onPressed: () async {
                                await _handleConfirmRequest(cartProvider);
                                setState(() {
                                  reachTime = 0;
                                  isSuccess = 1;
                                });
                                _inactivityTimer?.cancel();
                                _startInactivityTimer();
                              },
                              style: ElevatedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(
                                  vertical: 16,
                                  horizontal: 20,
                                ),
                                backgroundColor: Colors.redAccent,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(8),
                                ),
                              ),
                              child: const Text(
                                'Confirm Booking',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 24,
                                ),
                              ),
                            ),
                          ),

                          // 🔹 This Spacer eats any extra height ABOVE the map
                          const Spacer(),

                          // 🔹 Map is now pinned to the bottom of the screen
                          _buildMap(context),

                          const Spacer(),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ],
        ),
        backgroundColor: Colors.grey[100],
      ),
    );
  }

  // ========= MAP WIDGET =========
  Widget _buildMap(BuildContext context) {
    final double screenWidth = MediaQuery.of(context).size.width;
    final double screenHeight = MediaQuery.of(context).size.height;
    // Original image pixel coordinates where you want initial red dot
    // print(screenWidth);
    // print(screenHeight);
    final double initialX = screenWidth / 3.2;
    final double initialY = screenHeight / 4.1;
    // print(initialX);
    // print(initialY);

    return FutureBuilder<ImageInfo>(
      future: _getImageInfo('assets/images/MSBMap.png'),
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const SizedBox(
            height: 200,
            child: Center(child: CircularProgressIndicator()),
          );
        }

        final img = snapshot.data!;
        final double imgW = img.image.width.toDouble();
        final double imgH = img.image.height.toDouble();

        final aspectRatio = imgW / imgH;
        final double height = screenWidth / aspectRatio;

        // scale factors from image pixels -> displayed pixels
        final double scaleX = screenWidth / imgW;
        final double scaleY = height / imgH;

        // set initial marker once, if not set yet
        _markerPos ??= Offset(initialX * scaleX, initialY * scaleY);

        return SizedBox(
          width: screenWidth,
          height: height,
          child: Stack(
            children: [
              GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTapDown: (details) {
                  final local = details.localPosition;

                  // convert back to image coordinates
                  final double imgX = local.dx / scaleX;
                  final double imgY = local.dy / scaleY;

                  debugPrint(
                    'Tapped image coords: (${imgX.toStringAsFixed(1)}, ${imgY.toStringAsFixed(1)})',
                  );
                  Map<String, double> xy = convertToOXY(imgX, imgY);

                  /*showDialog(
                    context: context,
                    builder: (_) => AlertDialog(
                      title: const Text("OXY Coordinates"),
                      content: Text(
                        "x = ${xy["x"]!.toStringAsFixed(2)}\n"
                            "y = ${xy["y"]!.toStringAsFixed(2)}\n"
                            "width = ${imgX.toStringAsFixed(1)}\n"
                            "height = ${imgY.toStringAsFixed(1)}",
                        style: const TextStyle(fontSize: 20),
                      ),
                      actions: [
                        TextButton(
                          child: const Text("OK"),
                          onPressed: () => Navigator.of(context).pop(),
                        ),
                      ],
                    ),
                  );*/

                  setState(() {
                    this.x = xy["x"]!.toStringAsFixed(2);
                    this.y = xy["y"]!.toStringAsFixed(2);
                    _markerPos = local;
                    _imageX = imgX;
                    _imageY = imgY;
                  });
                },
                child: Image.asset(
                  'assets/images/MSBMap2.png',
                  width: screenWidth,
                  // height: screenHeight,
                  fit: BoxFit.fitWidth,
                ),
              ),

              // 🔴 single marker: initial + updated on tap
              if (_markerPos != null)
                Positioned(
                  left: _markerPos!.dx - 10,
                  top: _markerPos!.dy - 10,
                  child: _buildRedDot(),
                ),

              Positioned(
                left: 8,
                top: 8,
                child: Container(
                  width: 500,
                  height: 60,
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.6),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  // child: const Center(
                  child: Text(
                    "Press 🔴 in map to choose location",
                    // textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 30,
                      fontWeight: FontWeight.w600,
                      // ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildRedDot() {
    return Container(
      width: 20,
      height: 20,
      decoration: BoxDecoration(
        color: Colors.red,
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white, width: 2),
      ),
    );
  }

  Future<ImageInfo> _getImageInfo(String assetPath) async {
    final data = await rootBundle.load(assetPath);
    final codec = await ui.instantiateImageCodec(data.buffer.asUint8List());
    final frame = await codec.getNextFrame();
    return ImageInfo(image: frame.image);
  }

  Map<String, double> convertToOXY(double w, double h) {
    // Affine transform coefficients
    const double ax = -0.006225948;
    const double bx = -0.074317071;
    const double cx = 16.25728737;

    const double ay = -0.077398990;
    const double by = -0.009016770;
    const double cy = 30.58899320;

    final double x = ax * w + bx * h + cx;
    final double y = ay * w + by * h + cy;

    return {"x": x, "y": y};
  }
}

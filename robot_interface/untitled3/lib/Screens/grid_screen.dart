import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:untitled3/Screens/cart_screen.dart';
import 'package:untitled3/Screens/payment_screen.dart';
import 'package:untitled3/Services/LogService.dart';
import 'package:untitled3/enum/InteractionType.dart';
import '../Enum/AllActionInProject.dart';
import '../Enum/AllScreenInProject.dart';
import '../Services/ProductService.dart';
import '../models/cart.dart';
import '../models/products.dart';
import '../providers/cart_provider.dart';
import 'AllFaces/HappyFace.dart';
import '../widgets/sidebar.dart';
import '../Services/ControlCamera.dart';
import 'package:socket_io_client/socket_io_client.dart' as IO;

import 'order_screen.dart';

class GridPage extends StatefulWidget {
  const GridPage({super.key});

  @override
  State<GridPage> createState() => _RobotFaceState();
}

class _RobotFaceState extends State<GridPage>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _blink;

  @override
  void initState() {
    super.initState();

    print('🟢 initState: starting socket initialization');
    super.initState();
    _initSocket();
    _startOrResetTimer(); // Start timer at boot
    // LogService.postLogService(
    //   "Staying in FirstScreen & opening Camera",
    // );
    ControlCamera.callCameraAPI(action: 'stop', videourl: "None");
    _loadFakeData();


    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2500),
    )..repeat();

    _blink = TweenSequence<double>([
      TweenSequenceItem(tween: ConstantTween(1.0), weight: 60), // open
      TweenSequenceItem(
          tween: Tween(begin: 1.0, end: 0.1), weight: 20),       // closing
      TweenSequenceItem(
          tween: Tween(begin: 0.1, end: 1.0), weight: 20),       // opening
    ]).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    _cancelAutoCloseTimer();
    super.dispose();
  }

  int? selectedButtonIndex;
  Timer? _autoCloseTimer;
  bool showSidebar = false;
  late IO.Socket socket;
  final robotId = dotenv.env['ID_ROBOT'] ?? "1";
  List<Product> products = [];

  Timer? _autoHideTimer;

  void _startOrResetTimer() {
    _autoCloseTimer?.cancel();
    _autoCloseTimer = Timer(const Duration(seconds: 25), () {
      setState(() => showSidebar = false);
    });
  }

  void _cancelAutoCloseTimer() {
    _autoCloseTimer?.cancel();
  }

  Future<void> cleanupSocketAndNavigate() async {
    socket.off('TourchScreenAction');
    socket.off('connect');
    socket.off('disconnect');
    socket.off('connect_error');

    // await LogService.postLogService("Starting Record");

    if (!mounted) return;

    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => const OrderScreen(typeProduct: 0),
      ),
    );
  }

  Future<void> _loadFakeData() async {
    final jsonStr = await rootBundle.loadString('assets/data/fake_data.json');
    final Map<String, dynamic> data = jsonDecode(jsonStr);

    final List<Product> loadProducts = (data['inventory_items'] as List)
        .map((e) => Product.fromJson(e))
        .toList();

    setState(() {
      products = loadProducts;
    });
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
      cartProvider.clearCart();
      socket.off('TourchScreenAction');
      socket.off('connect');
      socket.off('disconnect');
      socket.off('connect_error');

      // ✅ Properly close the connection
      socket.disconnect();
      if (data['action'] == AllActionInproject.ADD.toString().split('.').last) {
        List<String> productNames = List<String>.from(data['value']['name']);
        List<int> quantities = List<int>.from(data['value']['quantity']);

        for (int i = 0; i < productNames.length; i++) {
          String name = productNames[i];

          for (Product p in products) {
            if (p.name == name && quantities[i] > 0) {
              cartProvider.addToCart(p, quantity: quantities[i]);
              break;
            }
          }
        }

        if (mounted) {
          LogService.postLogService("Starting Record");
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(builder: (_) => const CartScreen()),
          );
        }
      } else if (data['action'] ==
          AllActionInproject.MOVE.toString().split('.').last) {
        if (data['Move2Page'] ==
            AllScreenInProject.ORDERSCREEN.toString().split('.').last) {
          if (mounted) {
            LogService.postLogService("Starting Record");
            final int typeProduct = data['value'] != null ? data['value'] : 0;
            socket.off('TourchScreenAction');
            socket.off('connect');
            socket.off('disconnect');
            socket.off('connect_error');
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (_) => OrderScreen(typeProduct: typeProduct)),
            );
          }
        } else if (data['Move2Page'] ==
            AllScreenInProject.CARTSCREEN.toString().split('.').last) {
          if (mounted) {
            LogService.postLogService("Starting Record");
            socket.off('TourchScreenAction');
            socket.off('connect');
            socket.off('disconnect');
            socket.off('connect_error');
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (_) => const CartScreen()),
            );
          }
        } else if (data['Move2Page'] ==
            AllScreenInProject.PAYMENTSCREEN.toString().split('.').last) {
          if (mounted) {
            LogService.postLogService("Starting Record");
            socket.off('TourchScreenAction');
            socket.off('connect');
            socket.off('disconnect');
            socket.off('connect_error');
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (_) => const PaymentScreen()),
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
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.translucent,
      onTap: _startOrResetTimer,
      onPanDown: (_) => _startOrResetTimer(),
      child: Scaffold(
        body: Stack(
          children: [
            // background: animated robot face
            Positioned.fill(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  return AnimatedBuilder(
                    animation: _blink,
                    builder: (context, child) {
                      return CustomPaint(
                        painter: SimpleFacePainter(eyeOpen: _blink.value),
                        size: Size(
                          constraints.maxWidth,
                          constraints.maxHeight,
                        ),
                      );
                    },
                  );
                },
              ),
            ),

            // sidebar on top
            Positioned(
              top: 0,
              bottom: 0,
              left: 0,
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 10),
                width: showSidebar ? 200 : 50,
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
                    if (showSidebar)
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
                                onPressed: () => _onButtonPressed(0),
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
                          ],
                        ),
                      ),
                    Container(
                      width: 40,
                      alignment: Alignment.center,
                      child: IconButton(
                        iconSize: 50,
                        icon: Icon(
                          showSidebar
                              ? Icons.chevron_left
                              : Icons.chevron_right,
                        ),
                        color: Colors.white,
                        onPressed: () {
                          if (showSidebar) {
                            _cancelAutoCloseTimer();
                          }
                          setState(() => showSidebar = !showSidebar);
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

}

class SimpleFacePainter extends CustomPainter {
  final double eyeOpen; // 1 = open, 0.1 = almost closed

  SimpleFacePainter({required this.eyeOpen});

  @override
  void paint(Canvas canvas, Size size) {
    final Paint paint = Paint()..isAntiAlias = true;

    // Background
    canvas.drawRect(Offset.zero & size, paint..color = Colors.black);

    // ==== EYES ====
    final double eyeWidth = size.width * 0.22;
    final double eyeHeight = size.height * 0.20;
    final double eyeTop = size.height * 0.30;

    final Rect leftEye =
    Rect.fromLTWH(size.width * 0.18, eyeTop, eyeWidth, eyeHeight);
    final Rect rightEye =
    Rect.fromLTWH(size.width * 0.60, eyeTop, eyeWidth, eyeHeight);

    // eye whites
    paint.color = Colors.white;
    final Radius r = Radius.circular(size.width * 0.05);
    canvas.drawRRect(RRect.fromRectAndRadius(leftEye, r), paint);
    canvas.drawRRect(RRect.fromRectAndRadius(rightEye, r), paint);

    // pupils
    paint.color = Colors.lightBlueAccent;
    final double pupilRadius = eyeWidth * 0.18;
    canvas.drawCircle(leftEye.center, pupilRadius, paint);
    canvas.drawCircle(rightEye.center, pupilRadius, paint);

    // blinking lids
    final double coverHeight = eyeHeight * (1 - eyeOpen);
    if (coverHeight > 0) {
      paint.color = Colors.black;
      canvas.drawRect(
          Rect.fromLTWH(leftEye.left, leftEye.top, eyeWidth, coverHeight),
          paint);
      canvas.drawRect(
          Rect.fromLTWH(rightEye.left, rightEye.top, eyeWidth, coverHeight),
          paint);
    }

    // ==== MOUTH ====
    final Rect mouthRect = Rect.fromCenter(
      center: Offset(size.width / 2, size.height * 0.68),
      width: size.width * 0.55,
      height: size.height * 0.30,
    );

    paint
      ..color = Colors.white
      ..style = PaintingStyle.stroke
      ..strokeWidth = size.width * 0.012;

    final Path mouth = Path()
      ..arcTo(mouthRect, 0.20 * 3.14, 0.60 * 3.14, false);

    canvas.drawPath(mouth, paint);
  }

  @override
  bool shouldRepaint(covariant SimpleFacePainter oldDelegate) =>
      oldDelegate.eyeOpen != eyeOpen;
}

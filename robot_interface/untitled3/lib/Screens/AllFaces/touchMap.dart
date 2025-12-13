import 'dart:async';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class ChooseAddressOnMapScreen extends StatefulWidget {
  const ChooseAddressOnMapScreen({super.key});

  @override
  State<ChooseAddressOnMapScreen> createState() =>
      _ChooseAddressOnMapScreenState();
}

class _ChooseAddressOnMapScreenState extends State<ChooseAddressOnMapScreen> {
  final ScrollController _scrollController = ScrollController();

  // Map tap position
  Offset? _markerPos; // marker position on the displayed map
  double? _imageX, _imageY; // last coords in original image pixels (for debug)

  // Dropdown data (replace with your own)
  final List<String> summaryOptions = const [
    'Summary 1',
    'Summary 2',
    'Summary 3',
  ];
  String selectedSummary = 'Summary 1';

  // TODO: connect this to your real timer logic
  void _resetTimer() {
    // your idle timer reset here
  }

  // TODO: replace with your real confirm logic
  Future<void> _handleConfirmRequest(dynamic cartProvider) async {
    // Your implementation here
    await Future.delayed(const Duration(milliseconds: 300));
  }

  @override
  Widget build(BuildContext context) {
    // TODO: get your real cartProvider here (e.g. Provider.of<CartProvider>(context))

    return GestureDetector(
      behavior: HitTestBehavior.translucent,
      onTap: _resetTimer,
      onPanDown: (_) => _resetTimer(),
      child: Scaffold(
        appBar: AppBar(
          leadingWidth: 80,
          leading: Padding(
            padding: const EdgeInsets.only(left: 12.0),
            child: ElevatedButton.icon(
              onPressed: () {
                Navigator.of(context).pop(); // or pushReplacement to CartScreen
              },
              icon: const Icon(Icons.arrow_back, size: 28),
              label: const Text(""),
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
                  padding: const EdgeInsets.only(left: 16, right: 16, top: 16, bottom: 0),
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
                              onPressed: () {
                                // ...
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
    // final double initialX = screenWidth / 2.5;
    // final double initialY = screenHeight / 3.5;
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
        //_markerPos ??= Offset(initialX * scaleX, initialY * scaleY);

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
                  showDialog(
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
                  );

                  setState(() {
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

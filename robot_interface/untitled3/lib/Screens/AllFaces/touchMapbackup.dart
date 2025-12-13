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
  Offset? _markerPos;        // marker position on the displayed map
  double? _imageX, _imageY;  // last coords in original image pixels (for debug)

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
    final cartProvider = null;

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
                padding:
                const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
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
                  padding: const EdgeInsets.all(16),
                  child: ConstrainedBox(
                    constraints: BoxConstraints(
                      minHeight: constraints.maxHeight,
                    ),
                    child: IntrinsicHeight(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // ====== MAP HEADER ======
                          /*const Center(
                            child: Text(
                              "Tap anywhere on the map:",
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          const SizedBox(height: 10),*/

                          // ====== DROPDOWN CONTAINER ======
                          /*Container(
                            padding: const EdgeInsets.all(16),
                            margin: const EdgeInsets.only(bottom: 20),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(12),
                              boxShadow: const [
                                BoxShadow(
                                  color: Colors.black12,
                                  blurRadius: 6,
                                  offset: Offset(0, 2),
                                ),
                              ],
                            ),
                            child: SizedBox(
                              width: double.infinity,
                              child: DropdownButton<String>(
                                value: selectedSummary,
                                isExpanded: true,
                                items: summaryOptions.map((String value) {
                                  return DropdownMenuItem<String>(
                                    value: value,
                                    child: Center(
                                      child: Text(
                                        value,
                                        style: const TextStyle(
                                          fontSize: 24,
                                          fontWeight: FontWeight.bold,
                                        ),
                                        textAlign: TextAlign.center,
                                      ),
                                    ),
                                  );
                                }).toList(),
                                onChanged: (String? newValue) {
                                  if (newValue == null) return;
                                  setState(() {
                                    selectedSummary = newValue;
                                  });
                                },
                              ),
                            ),
                          ),

                          const SizedBox(height: 8),
*/
                          // ====== CONFIRM BUTTON ======
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton(
                              onPressed: () {
                                showDialog(
                                  context: context,
                                  barrierDismissible: false,
                                  builder: (dialogContext) {
                                    Future.delayed(
                                      const Duration(milliseconds: 100),
                                          () async {
                                        await _handleConfirmRequest(
                                          cartProvider,
                                        );

                                        if (dialogContext.mounted) {
                                          // TODO: remove or replace your socket off calls
                                          Navigator.of(dialogContext).pop();
                                          // TODO: navigate to your real GridPage here
                                          // Navigator.pushReplacement(
                                          //   context,
                                          //   MaterialPageRoute(
                                          //     builder: (_) => const GridPage(),
                                          //   ),
                                          // );
                                        }
                                      },
                                    );

                                    return const AlertDialog(
                                      title: Text('Booking Confirmed'),
                                      content: Text(
                                        'Thank you for your booking, products will transfer to your address soon',
                                      ),
                                      actions: [],
                                    );
                                  },
                                );
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

                          const SizedBox(height: 16),
                          const Spacer(),

                          // ====== MAP SECTION (FULL WIDTH, SHORTER HEIGHT) ======
                          _buildMap(context),

                          const SizedBox(height: 24),
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
    print(screenWidth);
    print(screenHeight);
    final double initialX = screenWidth/3;
    final double initialY = screenHeight/4;
    print(initialX);
    print(initialY);

    return FutureBuilder<ImageInfo>(
      future: _getImageInfo('assets/images/MSBMap.png'),
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const SizedBox(
            height: 300,
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
        _markerPos ??= Offset(
          initialX * scaleX,
          initialY * scaleY,
        );

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
                        )
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
                  height: screenHeight,
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
    // Coefficients from 3-point affine calibration
    const double ax = -0.00611462598;
    const double bx = -0.07489480695;
    const double cx = 16.12917217;

    const double ay = -0.07714377798;
    const double by = -0.00895836107;
    const double cy = 30.43565878;

    final double x = ax * w + bx * h + cx;
    final double y = ay * w + by * h + cy;

    return {"x": x, "y": y};
  }
}

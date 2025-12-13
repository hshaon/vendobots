import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: const Scaffold(
        backgroundColor: Colors.black,
        body: RobotFace(),
      ),
    );
  }
}

class RobotFace extends StatefulWidget {
  const RobotFace({super.key});

  @override
  State<RobotFace> createState() => _RobotFaceState();
}

class _RobotFaceState extends State<RobotFace>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _blink;

  @override
  void initState() {
    super.initState();

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
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return AnimatedBuilder(
          animation: _blink,
          builder: (context, child) {
            return CustomPaint(
              painter: SimpleFacePainter(eyeOpen: _blink.value),
              size: Size(constraints.maxWidth, constraints.maxHeight),
            );
          },
        );
      },
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

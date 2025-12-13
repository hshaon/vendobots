import 'package:flutter/material.dart';

/// Pixel robot face: only eyes + mouth
/// i = row index, j = column index, n = number of cells
/// eyesColor is used to indicate blinking:
///   - open  : eyesColor != Colors.black
///   - closed: eyesColor == Colors.black
Color RobotFace(int i, int j, int n, Color eyesColor) {
  final double row = i / n; // 0 → 1
  final double col = j / n; // 0 → 1

  // Quick flag for blink state
  final bool eyesClosed = eyesColor == Colors.black;

  // ===== EYES AREA (rectangles) =====
  final bool inLeftEyeRect =
      row > 0.30 && row < 0.50 && col > 0.18 && col < 0.38;
  final bool inRightEyeRect =
      row > 0.30 && row < 0.50 && col > 0.62 && col < 0.82;

  // Pupils (small boxes inside the eye when open)
  final bool inLeftPupil =
      row > 0.35 && row < 0.45 && col > 0.25 && col < 0.31;
  final bool inRightPupil =
      row > 0.35 && row < 0.45 && col > 0.69 && col < 0.75;

  // ===== MOUTH (simple curved line) =====
  // We approximate a smile with a small parabola around center (0.5, ~0.72)
  final double cx = 0.5;
  final double mouthWidth = 0.42;
  final double mouthHeight = 0.10;

  bool inMouth = false;
  if (col > cx - mouthWidth / 2 && col < cx + mouthWidth / 2) {
    final double dx = (col - cx) / (mouthWidth / 2); // -1..1
    final double yCurve =
        0.75 - mouthHeight * (1 - dx * dx); // smiling curve
    // thin band around that curve
    if (row > yCurve - 0.01 && row < yCurve + 0.01) {
      inMouth = true;
    }
  }

  // ===== COLORS =====
  // background
  Color bg = Colors.black;

  // Eyes
  if (inLeftEyeRect || inRightEyeRect) {
    if (eyesClosed) {
      // when blinking: whole eye becomes black (eyelid)
      return Colors.black;
    }
    // white eye area when open
    return Colors.white;
  }

  // Pupils only visible when open
  if (!eyesClosed && (inLeftPupil || inRightPupil)) {
    return Colors.lightBlueAccent;
  }

  // Mouth always white
  if (inMouth) {
    return Colors.white;
  }

  return bg;
}

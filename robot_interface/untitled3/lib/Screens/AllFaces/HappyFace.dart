import 'package:flutter/material.dart';

Color HappyFace(int i, int j, int n, Color happyColor) {
  // left eye
  if ((i > 2 / 10 * n && i < 4.5 / 10 * n) &&
      (j >= (2 * n / 10) && j <= (4 * n / 10))) {
    return happyColor;
  }
  // right eye
  if ((i > 2 / 10 * n && i < 4.5 / 10 * n) &&
      (j >= (6 * n / 10) && j <= (8 * n / 10))) {
    return happyColor;
  }

  double centerI = 7.0 / 10 * n;
  double centerJ = 5 / 10 * n;
  double radius = 2 / 10 * n;

  double dx = i - centerI;
  double dy = j - centerJ;
  double distance = dx * dx + dy * dy;

  if (distance < radius * radius && dx > 0) {
    return happyColor;
  }

  // default color
  return Colors.black;
}

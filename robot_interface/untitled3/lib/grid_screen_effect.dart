import 'dart:async';
import 'package:flutter/material.dart';
import 'package:untitled3/enum/InteractionType.dart';
import 'screens/AllFaces/HappyFace.dart';
import 'widgets/sidebar.dart';

class GridPage extends StatefulWidget {
  const GridPage({super.key});

  static const int numberOfCell = 100;

  @override
  State<GridPage> createState() => _GridPageState();
}

class _GridPageState extends State<GridPage> {
  bool showSidebar = false;
  Color eyesMonthColor = Colors.white;
  Timer? _timer;

  @override
  void initState() {
    super.initState();

    // Toggle eyesMonthColor every 2 seconds
    _timer = Timer.periodic(Duration(milliseconds: 1000), (timer) {
      setState(() {
        eyesMonthColor = (eyesMonthColor == Colors.white)
            ? Colors
                  .yellow // Bright pale yellow
            : Colors.white;
      });
    });
  }

  @override
  void dispose() {
    _timer?.cancel(); // Cancel timer when widget is disposed
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final cellWidth = size.width / GridPage.numberOfCell;
    final cellHeight = size.height / GridPage.numberOfCell;

    List<Widget> gridCells = [];

    for (int i = 0; i < GridPage.numberOfCell; i++) {
      for (int j = 0; j < GridPage.numberOfCell; j++) {
        gridCells.add(
          Container(
            alignment: Alignment.center,
            decoration: BoxDecoration(
              border: Border.all(
                color: HappyFace(i, j, GridPage.numberOfCell, eyesMonthColor),
              ),
              color: HappyFace(i, j, GridPage.numberOfCell, eyesMonthColor),
            ),
          ),
        );
      }
    }

    return Scaffold(
      body: Stack(
        children: [
          // Grid in the background
          Positioned.fill(
            child: GridView.count(
              crossAxisCount: GridPage.numberOfCell,
              physics: const NeverScrollableScrollPhysics(),
              padding: EdgeInsets.zero,
              childAspectRatio: cellWidth / cellHeight,
              children: gridCells,
            ),
          ),

          // Sidebar overlaid on top left
          Positioned(
            top: 0,
            bottom: 0,
            left: 0,
            child: SideBar(
              isVisible: showSidebar,
              interactionType: InteractionType.VOICE,
              onToggle: () {
                setState(() {
                  showSidebar = !showSidebar;
                });
              },
            ),
          ),
        ],
      ),
    );
  }
}

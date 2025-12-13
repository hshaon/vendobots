import 'package:flutter/material.dart';

class CategoryTabs extends StatelessWidget {
  final List<String> categories;
  final int selectedIndex;
  final Function(int) onTap;

  const CategoryTabs({
    super.key,
    required this.categories,
    required this.selectedIndex,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: categories.asMap().entries.map((entry) {
        final index = entry.key;
        final label = entry.value;
        final isSelected = selectedIndex == index;

        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
          child: ChoiceChip(
            label: Text(label, style: TextStyle(fontWeight: FontWeight.bold)),
            selected: isSelected,
            onSelected: (_) => onTap(index),
            selectedColor: Theme.of(context).colorScheme.primaryContainer,
          ),
        );
      }).toList(),
    );
  }
}

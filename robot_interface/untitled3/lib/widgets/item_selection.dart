import 'package:flutter/material.dart';

class ItemSelection extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;
  final List<String>? images;
  final bool selected;
  final VoidCallback onSelect;

  const ItemSelection({
    super.key,
    required this.icon,
    required this.title,
    required this.value,
    this.images,
    required this.selected,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onSelect,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: selected
              ? Theme.of(context).colorScheme.primary.withOpacity(0.1)
              : Colors.white,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: selected
                ? Theme.of(context).colorScheme.primary
                : Colors.grey.shade300,
            width: selected ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            Icon(
              icon,
              color: selected
                  ? Theme.of(context).colorScheme.primary
                  : Colors.grey,
              size: 28,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Row(
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: selected
                          ? FontWeight.bold
                          : FontWeight.normal,
                      color: selected
                          ? Theme.of(context).colorScheme.primary
                          : Colors.black87,
                    ),
                  ),
                  const SizedBox(width: 6),
                  if (images != null && images!.isNotEmpty && value == 'wallet')
                    Row(
                      children: images!
                          .map(
                            (img) => Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: Image.asset(
                                img,
                                width: 25,
                                height: 25,
                                fit: BoxFit.contain,
                              ),
                            ),
                          )
                          .toList(),
                    ),
                ],
              ),
            ),
            if (selected)
              const Icon(Icons.check_circle, color: Colors.redAccent),
          ],
        ),
      ),
    );
  }
}

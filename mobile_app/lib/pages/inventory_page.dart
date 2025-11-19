import 'package:flutter/material.dart';
import '../models/inventory_item.dart'; // Import the model
import '../services/api_service.dart'; // Import the service

class InventoryPage extends StatefulWidget {
  const InventoryPage({super.key});

  @override
  State<InventoryPage> createState() => _InventoryPageState();
}

class _InventoryPageState extends State<InventoryPage> {
  // 1. Create a Future for your data
  late Future<List<InventoryItem>> futureInventoryItems;
  final ApiService apiService = ApiService();

  // Mock robot data (can be replaced by API call later)
  String robotName = "VendorBot-01";
  String status = "Stocked";

  // 2. Fetch data in initState
  @override
  void initState() {
    super.initState();
    futureInventoryItems = apiService.getInventoryItems();
  }

  // ... (Your robot info section remains the same) ...
  
  @override
  Widget build(BuildContext context) {
    Color statusColor = (status == "Stocked")
        ? Colors.green
        : (status == "Restocking" ? Colors.amber : Colors.red);
        
    // 3. Return your page UI
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // --- Robot Info Section (Stays the same for now) ---
          CircleAvatar(
            radius: 50,
            backgroundImage: const AssetImage('assets/robot.jpg'),
            onBackgroundImageError: (_, __) {},
            backgroundColor: Colors.grey.shade300,
            child: const Icon(Icons.smart_toy, size: 50, color: Colors.white),
          ),
          const SizedBox(height: 12),
          Text(robotName, style: Theme.of(context).textTheme.headlineSmall!.copyWith(fontWeight: FontWeight.bold)),
          // ... (rest of robot info)
          const SizedBox(height: 20),

          // --- Summary Card (We can update this inside the FutureBuilder) ---
          
          // 4. Use FutureBuilder to display data
          FutureBuilder<List<InventoryItem>>(
            future: futureInventoryItems,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                // While data is loading
                return const Center(child: CircularProgressIndicator());
              } else if (snapshot.hasError) {
                // If an error occurred
                return Center(child: Text("Error: ${snapshot.error}"));
              } else if (snapshot.hasData) {
                // When data is available
                final inventoryItems = snapshot.data!;
                
                return Column(
                  children: [
                    // --- Summary Card ---
                    Card(
                      elevation: 3,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 24),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text("Items Loaded: ${inventoryItems.length}", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                            Text(
                              "Low Stock: ${inventoryItems.where((i) => i.quantity <= 3).length}",
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // --- Inventory List ---
                    ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: inventoryItems.length,
                      itemBuilder: (context, index) {
                        final item = inventoryItems[index];
                        return _inventoryCard(
                          // Use data from the API
                          name: item.name,
                          price: item.price ?? 0.0,
                          count: item.quantity,
                          image: item.imageUrl ?? 'assets/placeholder.jpg', // Use placeholder if no image
                        );
                      },
                    ),
                  ],
                );
              } else {
                // Default case
                return const Center(child: Text("No items found."));
              }
            },
          ),
        ],
      ),
    );
  }

  // Helper widget for each inventory item
  Widget _inventoryCard({
    required String name,
    required double price,
    required int count,
    required String image,
  }) {
    bool isLowStock = count <= 3;
    bool isHttpImage = image.startsWith('http');

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 10),
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              // Use Image.network for web images, Image.asset for local
              child: isHttpImage
                  ? Image.network(
                      image,
                      width: 80,
                      height: 80,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) =>
                          Container(width: 80, height: 80, color: Colors.grey[300], child: const Icon(Icons.fastfood, size: 40, color: Colors.white)),
                    )
                  : Image.asset(
                      image, // Assumes a local placeholder
                      width: 80,
                      height: 80,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) =>
                          Container(width: 80, height: 80, color: Colors.grey[300], child: const Icon(Icons.fastfood, size: 40, color: Colors.white)),
                    ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(name, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  Text("\$${price.toStringAsFixed(2)}", style: const TextStyle(fontSize: 16, color: Colors.teal)),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const Icon(Icons.inventory_2, size: 16),
                      const SizedBox(width: 4),
                      Text(
                        "Count: $count",
                        style: TextStyle(
                          color: isLowStock ? Colors.red : Colors.black,
                          fontWeight: isLowStock ? FontWeight.bold : FontWeight.normal,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            // ... (rest of card)
          ],
        ),
      ),
    );
  }
}
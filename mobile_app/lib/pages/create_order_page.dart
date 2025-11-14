// mobile_app/lib/pages/create_order_page.dart
import 'package:flutter/material.dart';
import '../models/inventory_item.dart';
import '../models/robot.dart';
import '../models/delivery_record.dart';
import '../services/api_service.dart';
import 'map_page.dart';
import 'order_confirmation_page.dart';

class CreateOrderPage extends StatefulWidget {
  final Robot robot;
  const CreateOrderPage({super.key, required this.robot});

  @override
  State<CreateOrderPage> createState() => _CreateOrderPageState();
}

class _CreateOrderPageState extends State<CreateOrderPage> {
  final ApiService apiService = ApiService();
  late Future<List<InventoryItem>> futureInventory;
  
  // This state holds the "shopping cart"
  // Map<ItemID, Quantity>
  final Map<int, int> _cart = {};
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    // You need to add getInventoryItems() to your ApiService!
    futureInventory = apiService.getInventoryItems();
  }

  void _updateCart(int itemId, int quantity) {
    setState(() {
      if (quantity <= 0) {
        _cart.remove(itemId);
      } else {
        _cart[itemId] = quantity;
      }
    });
  }

  // --- NAVIGATION & ORDER LOGIC ---
  Future<void> _selectLocationAndPlaceOrder() async {
    if (_cart.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select at least one item.')),
      );
      return;
    }

    // 1. Push to MapPage to get a location
    final Offset? selectedLocation = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => MapPage(
          // We pass the robot to MapPage so it can show its current location
          robot: widget.robot, 
          // Tell MapPage it's in "picker mode"
          isPickerMode: true,
        ),
      ),
    );

    // 2. If the user selected a location (didn't just press "back")
    if (selectedLocation != null && mounted) {
      setState(() { _isLoading = true; });

      // 3. Prepare data for the API
      final String inventoryIds = _cart.keys.map((id) => id.toString()).toList().toString();
      final String quantity = _cart.values.map((qty) => qty.toString()).toList().toString();

      try {
        // 4. Create the delivery record
        final DeliveryRecord newRecord = await apiService.createDelivery(
          robotId: widget.robot.id,
          message: "New order from app",
          address: "Map Selection",
          inventoryIds: inventoryIds,
          quantity: quantity,
          status: "WAITING",
          startX: widget.robot.currentPosX,
          startY: widget.robot.currentPosY,
          destX: selectedLocation.dx,
          destY: selectedLocation.dy,
        );

        // 5. Navigate to confirmation page, clearing the order stack
        if (mounted) {
          Navigator.pushAndRemoveUntil(
            context,
            MaterialPageRoute(
              builder: (context) => OrderConfirmationPage(
                confirmationCode: newRecord.confirmationCode ?? "ERROR",
              ),
            ),
            (route) => route.isFirst, // Removes all pages until the dashboard
          );
        }

      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed to place order: $e')),
          );
        }
      } finally {
        if (mounted) {
          setState(() { _isLoading = false; });
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Create Order'),
      ),
      body: Stack(
        children: [
          FutureBuilder<List<InventoryItem>>(
            future: futureInventory,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return Center(child: Text('Error: ${snapshot.error}'));
              }
              if (!snapshot.hasData || snapshot.data!.isEmpty) {
                return const Center(child: Text('No inventory items found.'));
              }

              final items = snapshot.data!;
              return ListView.builder(
                itemCount: items.length,
                itemBuilder: (context, index) {
                  final item = items[index];
                  final inCartQty = _cart[item.id] ?? 0;
                  
                  return Card(
                    margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundImage: NetworkImage(item.imageUrl ?? ''),
                        onBackgroundImageError: (_, __) {},
                        child: (item.imageUrl == null) ? const Icon(Icons.inventory_2) : null,
                      ),
                      title: Text(item.name),
                      subtitle: Text('\$${item.price?.toStringAsFixed(2)} - ${item.quantity} in stock'),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.remove_circle),
                            onPressed: (inCartQty > 0)
                                ? () => _updateCart(item.id, inCartQty - 1)
                                : null,
                          ),
                          Text(inCartQty.toString(), style: Theme.of(context).textTheme.titleMedium),
                          IconButton(
                            icon: const Icon(Icons.add_circle),
                            onPressed: (inCartQty < item.quantity)
                                ? () => _updateCart(item.id, inCartQty + 1)
                                : null,
                          ),
                        ],
                      ),
                    ),
                  );
                },
              );
            },
          ),
          if (_isLoading)
            Container(
              color: Colors.black.withOpacity(0.5),
              child: const Center(child: CircularProgressIndicator()),
            ),
        ],
      ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.all(16.0),
        child: FilledButton.icon(
          icon: const Icon(Icons.location_on),
          label: const Text('Select Delivery Location'),
          style: FilledButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
          onPressed: _isLoading ? null : _selectLocationAndPlaceOrder,
        ),
      ),
    );
  }
}
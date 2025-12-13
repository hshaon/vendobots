import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:provider/provider.dart';
import 'package:untitled3/screens/payment_screen.dart';
import 'package:socket_io_client/socket_io_client.dart' as IO;

import '../Enum/AllActionInProject.dart';
import '../Enum/AllScreenInProject.dart';
import '../Services/ControlCamera.dart';
import '../Services/DeliveryRecordService.dart';
import '../Services/LogService.dart';
import '../Services/ProductService.dart';
import '../models/cart.dart';
import '../models/products.dart';
import '../providers/cart_provider.dart';
import 'grid_screen.dart';
import 'order_screen.dart';

class CartScreen extends StatefulWidget {
  const CartScreen({super.key});

  @override
  State<CartScreen> createState() => _CartScreenState();
}

class _CartScreenState extends State<CartScreen> {
  final robotId = dotenv.env['ID_ROBOT'] ?? "1";
  late IO.Socket socket;
  Timer? _inactivityTimer;
  late int reachTime = 60;

  @override
  void initState() {
    super.initState();
    _initSocket();
    _startInactivityTimer();
    LogService.postLogService(
      "Staying in CartScreen",
    );
  }

  void _startInactivityTimer() {
    _inactivityTimer?.cancel();

    _inactivityTimer = Timer(Duration(seconds: reachTime), () async {
      if (!mounted) return;

      // Show a blocking loading dialog
      /*showDialog(
        context: context,
        barrierDismissible: false, // prevent user from closing it
        builder: (context) {
          return AlertDialog(
            backgroundColor: Colors.white,
            title: const Text(
              "System Restarting",
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            content: const Text(
              "Please wait a moment, the system is restarting...",
              style: TextStyle(fontSize: 16),
            ),
          );
        },
      );*/
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) {
          return WillPopScope(
            onWillPop: () async => false, // disable back button
            child: const AlertDialog(
              backgroundColor: Colors.white,
              title: Text(
                "System Restarting",
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    "Please wait a moment, the system is restarting...",
                    style: TextStyle(fontSize: 16),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          );
        },
      );

      String v_url = await DeliveryRecordService.handleFailCase();
      //ControlCamera.callCameraAPI(action: 'stop', videourl: v_url);
      LogService.postLogService("Canceled transaction and stop record by camera!");
      // ✅ Give UI time to render the dialog first
      await Future.delayed(const Duration(milliseconds: 100));
      // Add a short delay to let the loading show before navigating
      //await Future.delayed(const Duration(seconds: 1));

      if (mounted) {
        final cartProvider = Provider.of<CartProvider>(context, listen: false);
        cartProvider.clearCart();
        Navigator.of(
          context,
        ).pushReplacement(MaterialPageRoute(builder: (_) => const GridPage()));
      }
    });
  }

  void _resetTimer() {
    _startInactivityTimer();
  }

  void _initSocket() {
    socket = IO.io(
      'https://hricameratest.onrender.com',
      IO.OptionBuilder()
          .setTransports(['websocket'])
          .enableReconnection()
          .disableAutoConnect()
          .build(),
    );

    socket.onConnect((_) {
      print('✅ Connected to server');
      socket.emit('join', {'room': robotId});
    });

    final cartProvider = Provider.of<CartProvider>(context, listen: false);
    socket.on('TourchScreenAction', (data) async {
      if (data['action'] ==
          AllActionInproject.REMOVE.toString().split('.').last) {
        if (!mounted) return;
        cartProvider.clearCart();
      } else if (data['action'] ==
          AllActionInproject.ADD.toString().split('.').last) {
        List<String> productNames = List<String>.from(data['value']['name']);
        List<int> quantities = List<int>.from(data['value']['quantity']);

        for (int i = 0; i < productNames.length; i++) {
          String name = productNames[i];
          bool updateActivated = false;

          for (CartItem item in cartProvider.items) {
            if (item.product.name == name) {
              // cartProvider.removeFromCart(item.product);
              if (quantities[i] > 0) {
                cartProvider.updateQuantity(
                  item.product,
                  item.quantity + quantities[i],
                );
              } else {
                cartProvider.removeFromCart(item.product);
              }
              updateActivated = true;
            }
          }

          if (updateActivated == false) {
            List<Product> products = await ProductService.fetchProducts();
            for (Product p in products) {
              if (p.name == name && quantities[i] > 0) {
                cartProvider.addToCart(p, quantity: quantities[i]);
                break;
              }
            }
          }
        }
      } else if (data['action'] ==
          AllActionInproject.UPDATE.toString().split('.').last) {
        List<String> productNames = List<String>.from(data['value']['name']);
        List<int> quantities = List<int>.from(data['value']['quantity']);
        for (int i = 0; i < productNames.length; i++) {
          String name = productNames[i];
          for (CartItem item in cartProvider.items) {
            if (item.product.name == name) {
              // cartProvider.removeFromCart(item.product);
              if (quantities[i] > 0)
                cartProvider.updateQuantity(item.product, quantities[i]);
              else
                cartProvider.removeFromCart(item.product);
            }
          }
        }
      } else if (data['action'] ==
          AllActionInproject.MOVE.toString().split('.').last) {

        socket.off('TourchScreenAction');
        socket.off('connect');
        socket.off('disconnect');
        socket.off('connect_error');

        // ✅ Properly close the connection
        socket.disconnect();
        if (data['Move2Page'] ==
            AllScreenInProject.ORDERSCREEN.toString().split('.').last) {
          final int typeProduct = data['value'] != null ? data['value'] : 0;
          if (mounted) {
            socket.off('TourchScreenAction');
            socket.off('connect');
            socket.off('disconnect');
            socket.off('connect_error');
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (_) => OrderScreen(typeProduct: typeProduct)),
            );
          }
        // } else if (data['Move2Page'] ==
        //     AllScreenInProject.HOMEPAGESCREEN.toString().split('.').last) {
        //   if (mounted) {
        //     socket.off('TourchScreenAction');
        //     socket.off('connect');
        //     socket.off('disconnect');
        //     socket.off('connect_error');
        //     ControlCamera.callCameraAPI(action: 'stop', videourl: "None");
        //     LogService.postLogService(
        //       "Staying in FirstScreen",
        //     );
        //     Navigator.of(context).pushReplacement(
        //       MaterialPageRoute(builder: (_) => const GridPage()),
        //     );
        //   }
        } else if (data['Move2Page'] ==
            AllScreenInProject.PAYMENTSCREEN.toString().split('.').last) {
          if (mounted) {
            socket.off('TourchScreenAction');
            socket.off('connect');
            socket.off('disconnect');
            socket.off('connect_error');
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (_) => const PaymentScreen()),
            );
          }
        }
      }
    });

    socket.onConnectError((err) => print('⚠️ Connect error: $err'));
    socket.onDisconnect((_) => print('❌ Disconnected'));

    socket.connect();
  }

  @override
  void dispose() {
    // socket.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cartProvider = Provider.of<CartProvider>(context);

    return GestureDetector(
      behavior: HitTestBehavior.translucent,
      onTap: _resetTimer,
      onPanDown: (_) => _resetTimer(),
      child: Scaffold(
        appBar: AppBar(
          leadingWidth: 80, // make space for bigger button
          leading: Padding(
            padding: const EdgeInsets.only(left: 12.0),
            child: ElevatedButton.icon(
              onPressed: () {
                socket.off('TourchScreenAction');
                socket.off('connect');
                socket.off('disconnect');
                socket.off('connect_error');

                // ✅ Properly close the connection
                socket.disconnect();

                Navigator.of(context).pushReplacement(
                  MaterialPageRoute(builder: (_) => const OrderScreen(typeProduct: 0,)),
                );
              },
              icon: const Icon(Icons.arrow_back, size: 28), // bigger icon
              label: const Text(
                "",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
              ),
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
          title: const Text('Your cart', style: TextStyle(fontSize: 32)),
          centerTitle: true,
        ),
        body: Listener(
          onPointerDown: (_) => () {},
          behavior: HitTestBehavior.translucent,
          child: cartProvider.items.isEmpty
              ? const Center(
                  child: Text(
                    'You didn\'t choose anything',
                    style: TextStyle(fontSize: 18),
                  ),
                )
              : Column(
                  children: [
                    SizedBox(height: 20),
                    Expanded(
                      child: ListView.builder(
                        itemCount: cartProvider.items.length,
                        itemBuilder: (context, index) {
                          final cartItem = cartProvider.items[index];
                          final product = cartItem.product;

                          return Card(
                            margin: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 6,
                            ),
                            child: ListTile(
                              leading: Image.network(
                                product.imagePath,
                                width: 100,
                                height: 100,
                                fit: BoxFit.contain,
                              ),
                              title: Text(product.name),
                              subtitle: Text(
                                '\$${product.price.toStringAsFixed(2)}',
                                style: const TextStyle(color: Colors.grey),
                              ),
                              trailing: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  IconButton(
                                    icon: const Icon(
                                      Icons.remove_circle_outline,
                                    ),
                                    onPressed: () {
                                      cartProvider.removeFromCart(product);
                                    },
                                  ),
                                  Text(
                                    '${cartItem.quantity}',
                                    style: const TextStyle(fontSize: 16),
                                  ),
                                  IconButton(
                                    icon: const Icon(Icons.add_circle_outline),
                                    onPressed: () {
                                      cartProvider.addToCart(product);
                                    },
                                  ),

                                  IconButton(
                                    onPressed: () {
                                      cartProvider.removeFromCart(
                                        product,
                                        isRemoveItem: true,
                                      );
                                    },
                                    icon: const Icon(
                                      Icons.delete,
                                      color: Colors.red,
                                    ),
                                    style: IconButton.styleFrom(
                                      backgroundColor: Colors.red.shade100,
                                      hoverColor: Colors.red.shade200,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                    _buildBottomBar(cartProvider),
                  ],
                ),
        ),
      ),
    );
  }

  // Gia lap dat hang
  Widget _buildBottomBar(CartProvider cartProvider) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(
        color: Colors.blueAccent.withOpacity(0.05),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            'Total: \$${cartProvider.totalPrice.toStringAsFixed(2)}',
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          ElevatedButton.icon(
            onPressed: () {
              if (cartProvider.items.isNotEmpty) {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (_) => const PaymentScreen()),
                );
              }
            },
            icon: const Icon(Icons.shopping_cart_checkout),
            label: const Text('Checkout'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            ),
          ),
        ],
      ),
    );
  }

  // clear cart khi order
  // void _handleCheckout(CartProvider cartProvider) async {
  //   final confirmed = await showDialog<bool>(
  //     context: context,
  //     builder: (context) => AlertDialog(
  //       title: const Text('Order confirm'),
  //       content: const Text('Are you sure you want to order?'),
  //       actions: [
  //         TextButton(
  //           onPressed: () => Navigator.pop(context, false),
  //           child: const Text('Cancel'),
  //         ),
  //         ElevatedButton(
  //           onPressed: () => Navigator.pop(context, true),
  //           child: const Text('Order now'),
  //         ),
  //       ],
  //     ),
  //   );

  //   if (confirmed == true) {
  //     cartProvider.clearCart();
  //     if (mounted) {
  //       ScaffoldMessenger.of(
  //         context,
  //       ).showSnackBar(const SnackBar(content: Text('Order Successfully!')));
  //     }
  //   }
  // }
}

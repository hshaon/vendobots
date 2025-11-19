// mobile_app/lib/pages/order_confirmation_page.dart
import 'package:flutter/material.dart';

class OrderConfirmationPage extends StatelessWidget {
  final String confirmationCode;

  const OrderConfirmationPage({super.key, required this.confirmationCode});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Order Confirmed!'),
        automaticallyImplyLeading: false, // No "back" button
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.check_circle,
                color: Colors.green,
                size: 100,
              ),
              const SizedBox(height: 24),
              Text(
                'Your order has been placed!',
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              const Text(
                'Please enter this 6-digit code at the robot to receive your items:',
                style: TextStyle(fontSize: 16),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                decoration: BoxDecoration(
                  color: Colors.grey.shade200,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.shade400),
                ),
                child: Text(
                  confirmationCode,
                  style: const TextStyle(
                    fontSize: 48,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 8, // Spreads the numbers out
                  ),
                ),
              ),
              const SizedBox(height: 48),
              FilledButton.icon(
                icon: const Icon(Icons.home),
                label: const Text('Back to Dashboard'),
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 32),
                ),
                onPressed: () {
                  // Go back to the dashboard (the first page)
                  Navigator.popUntil(context, (route) => route.isFirst);
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}
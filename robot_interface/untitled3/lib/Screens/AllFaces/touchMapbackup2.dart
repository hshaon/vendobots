// SizedBox(
// width: double.infinity,
// child: ElevatedButton(
// onPressed: () {
// showDialog(
// context: context,
// barrierDismissible: false,
// builder: (dialogContext) {
// Future.delayed(
// const Duration(milliseconds: 100),
// () async {
// await _handleConfirmRequest(
// cartProvider,
// );
//
// if (dialogContext.mounted) {
// // TODO: remove or replace your socket off calls
// Navigator.of(dialogContext).pop();
// // TODO: navigate to your real GridPage here
// // Navigator.pushReplacement(
// //   context,
// //   MaterialPageRoute(
// //     builder: (_) => const GridPage(),
// //   ),
// // );
// }
// },
// );
//
// return const AlertDialog(
// title: Text('Booking Confirmed'),
// content: Text(
// 'Thank you for your booking, products will transfer to your address soon',
// ),
// actions: [],
// );
// },
// );
// },
// style: ElevatedButton.styleFrom(
// padding: const EdgeInsets.symmetric(
// vertical: 16,
// horizontal: 20,
// ),
// backgroundColor: Colors.redAccent,
// shape: RoundedRectangleBorder(
// borderRadius: BorderRadius.circular(8),
// ),
// ),
// child: const Text(
// 'Confirm Booking',
// style: TextStyle(
// color: Colors.white,
// fontSize: 24,
// ),
// ),
// ),
// ),
//
// // const SizedBox(height: 16),
// // const Spacer(),
//
// // ====== MAP SECTION (FULL WIDTH, SHORTER HEIGHT) ======
// _buildMap(context),
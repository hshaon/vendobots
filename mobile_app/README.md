VendoBot Mobile Application
This directory contains the cross-platform Flutter application for the VendoBot project. This app serves as the primary control panel for monitoring robot status, viewing inventory, and (in the future) managing orders.
Current Features
Dashboard: A real-time dashboard showing the primary robot's status, battery level, and a live-updating list of recent activity logs.
Inventory: Fetches and displays the complete list of items currently stocked in the robot, including name, price, and quantity.
Map View: Placeholder page for future real-time robot SLAM/navigation map display.
Settings: Placeholder page for user preferences.
(Future features will include product browsing, order placement, and payments.)
Tech Stack
Flutter: Cross-platform UI toolkit for Android, iOS, Web, and Desktop.
Dart: Language
http package: For making REST API calls to the backend server.
Setup & Run Instructions
This application requires the backend_server to be running to function correctly.
1. Run the Backend First
Before launching the app, make sure you have the backend server running.
Follow the setup instructions in that directory: ../backend_server/README.md
2. Run the Flutter App
Navigate to this directory:
cd mobile_app


Get Dependencies:
flutter pub get


Run the App:
You can run this app on multiple platforms.
For Web (Recommended for quick testing):
flutter run -d chrome


For PC (Windows/macOS/Linux):
flutter run -d windows
# or -d macos / -d linux


For Android Emulator:
flutter run


Connecting to the API
The app is designed to automatically find the correct backend IP address depending on how you run it. This logic is handled in: lib/services/api_service.dart.
Web & PC: Connects to http://127.0.0.1:8000
Android Emulator: Connects to http://10.0.2.2:8000
Real Android Device: This requires manual configuration.
Find your PC's local network IP (e.g., 192.168.1.10).
Start the backend server on 0.0.0.0 (uvicorn app.main:app --reload --host 0.0.0.0).
Open lib/services/api_service.dart, set IS_REAL_ANDROID_DEVICE = true, and update the PC_LOCAL_IP variable.

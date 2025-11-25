VendoBot Backend Server

This directory contains the FastAPI backend for the VendoBot project. It manages robot status, inventory, and logs, providing a REST API for the mobile app.

Project Structure

/app: Main application source code.

/routers: API endpoint definitions (robots, inventory, logs).

crud.py: Database create, read, update, delete functions.

database.py: Database connection and session management.

main.py: Main FastAPI app instance, CORS, and router inclusion.

models.py: SQLAlchemy database table definitions.

schemas.py: Pydantic data models for API validation.

requirements.txt: Python package dependencies.

Setup Instructions

Follow these steps to get the server running on your local machine.

1. Prerequisites

Python 3.9+

PostgreSQL: A running PostgreSQL server. You can install it from postgresql.org.

2. Install Python Dependencies

Clone the Repo:

git clone [https://github.com/hshaon/vendobots.git]
cd vendobots/backend_server


Create a Virtual Environment:

# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate


Install Packages:

pip install -r requirements.txt


3. Set Up the PostgreSQL Database

Open psql (or your preferred SQL tool like pgAdmin).

Create the Database:

CREATE DATABASE vendor_bot;


Connect to the Database (\c vendor_bot) and run the following SQL commands to create the tables:

-- Table for robots
CREATE TABLE robots (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  image_url TEXT,
  status VARCHAR(50) DEFAULT 'idle', -- e.g. idle, charging, delivering
  battery_level INT DEFAULT 100,
  current_pos_x FLOAT,
  current_pos_y FLOAT,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for items in inventory
CREATE TABLE inventory_items (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  image_url TEXT,
  price DECIMAL(10, 2),
  quantity INT DEFAULT 0,
  category VARCHAR(100)
  robot_id INT REFERENCES robots(id) ON DELETE SET NULL
);

-- Table for logs (robot actions, deliveries)
CREATE TABLE robot_logs (
  id SERIAL PRIMARY KEY,
  robot_id INT REFERENCES robots(id),
  message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Table for delivery records (robot actions, deliveries)
CREATE TABLE delivery_records (
  id SERIAL PRIMARY KEY,
  robot_id INT REFERENCES robots(id),
  address TEXT,
  status TEXT,
  message TEXT,
  videourl TEXT,
  inventory_ids TEXT,
  Quantity TEXT,

  start_pos_x FLOAT,
  start_pos_y FLOAT,
  dest_pos_x FLOAT
  dest_pos_y FLOAT

  confirmation_code TEXT,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

4. Configure Environment

Create a new file in this directory named .env.

Copy the content from .env.example (or the block below) and update it with your PostgreSQL username, password, and database name.

Contents for .env:

# .env
# Update with your local PostgreSQL credentials
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@127.0.0.1:5432/vendor_bot


Note: The .gitignore file will prevent this file from being uploaded to GitHub.

5. Run the Server

With your virtual environment still active, run uvicorn:

uvicorn app.main:app --reload

(potentially need to set env variable with $env:DATABASE_URL="postgresql://postgres:102403@127.0.0.1:5432/vendor_bot"; uvicorn app.main:app --reload)

The server is now running! You can view the interactive API documentation at:
http://127.0.0.1:8000/docs
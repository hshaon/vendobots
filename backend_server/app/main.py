print("Starting FastAPI app...")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.routers import robots, inventory, logs, deliveryRecord, control
from app import database, models, crud, schemas

def seed_initial_data():
    db = database.SessionLocal()
    try:
        # Check and Seed ROBOTS
        if crud.get_robots_count(db) == 0: # 👈 Use the new count function
            print("Database is empty. Creating default robot...")
            robot_data = schemas.RobotCreate(
                name="VendorBot Alpha",
                image_url="https://vendorbot.com/images/alpha.png",
                status="idle",
                battery_level=95
            )
            crud.create_robot(db, robot_data)
            db.commit() # Commit the robot to ensure it gets an ID (needed for inventory foreign key)
            print("Default robot created successfully.")
        else:
            print("Robots already exist. Skipping robot seeding.")

        # Check and Seed INVENTORY
        if crud.get_inventory_count(db) == 0:
            print("Inventory table is empty. Loading data from CSV...")
            crud.seed_inventory_from_csv(db)
            db.commit() # Commit the inventory items
            print("Inventory seeding complete.")
        else:
            print("Inventory items already exist. Skipping inventory seeding.")

    except Exception as e:
        db.rollback()
        print(f"Error in initial data seeding: {e}")
    finally:
        db.close()

try:
    print("Attempting to create database tables...")
    models.Base.metadata.create_all(bind=database.engine)
    print("Database tables checked/created.")
    
    seed_initial_data()
except Exception as e:
    print(f"Error creating database tables: {e}")


app = FastAPI(title="Vendor Bot API")
print("FastAPI app instance created.")


origins = [
    "*"  # This means "Allow All"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Allows specific origins
    allow_credentials=True,
    allow_methods=["*"],         # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],         # Allows all headers
)
# ----------------------------------------


try:
    # 3. Include your routers *after* adding the middleware
    app.include_router(robots.router)
    app.include_router(inventory.router)
    app.include_router(logs.router)
    app.include_router(deliveryRecord.router)
    app.include_router(control.router)
    print("Routers imported successfully")
except Exception as e:
    print("Error importing routers:", e)


# 4. Your root endpoint for testing
@app.get("/")
def read_root():
    return {"message": "Welcome to the Vendor Bot API"}

from sqlalchemy.orm import Session
from . import models, schemas
import csv
import os
from decimal import Decimal
from datetime import datetime
import random

def get_robots(db: Session):
    return db.query(models.Robot).all()

def get_robot_by_id(db: Session, robot_id: int):
    return db.query(models.Robot).filter(models.Robot.id == robot_id).first()


def create_robot(db: Session, robot: schemas.RobotCreate):
    new_robot = models.Robot(**robot.model_dump())
    db.add(new_robot)
    db.commit()
    db.refresh(new_robot)
    return new_robot

def get_inventory(db: Session):
    return db.query(models.InventoryItem).all()

def create_inventory_item(db: Session, item: schemas.InventoryItemCreate):
    db_item = models.InventoryItem(
        **item.model_dump(exclude_unset=True)
    )
    # Convert Pydantic float back to Decimal for the model if needed
    if item.price is not None:
        db_item.price = Decimal(str(item.price))

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_inventory_count(db: Session) -> int:
    """Returns the total number of inventory items in the database."""
    return db.query(models.InventoryItem).count()

def seed_inventory_from_csv(db: Session):
    """Reads inventory_items.csv and seeds the database."""
    
    # 1. Construct the path to the CSV file
    # Get the current file's directory (app/crud.py)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, 'sampleDataInDB', 'inventory_items.csv')

    print(f"Attempting to load inventory from: {csv_path}")

    try:
        with open(csv_path, mode='r', newline='', encoding='utf-8') as file:
            # Use DictReader to easily access columns by header name
            reader = csv.DictReader(file)
            
            for row in reader:
                # 2. Map CSV data to the Pydantic schema
                item_data = schemas.InventoryItemCreate(
                    name=row.get('name'),
                    image_url=row.get('image_url'),
                    # Convert string values to correct Python types expected by Pydantic
                    price=float(row.get('price', 0.00)), 
                    quantity=int(row.get('quantity', 0)),
                    category=row.get('category'),
                    robot_id=int(row.get('robot_id')) if row.get('robot_id') else None
                )
                
                # 3. Create the database entry
                create_inventory_item(db, item_data)
        
        print(f"Successfully seeded {db.query(models.InventoryItem).count()} inventory items.")

    except FileNotFoundError:
        print(f"ERROR: CSV file not found at {csv_path}. Skipping inventory seeding.")
    except Exception as e:
        db.rollback()
        print(f"ERROR during inventory seeding: {e}")

def create_log(db: Session, log: schemas.RobotLogCreate):
    new_log = models.RobotLog(**log.model_dump())
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

def create_delivery_record(db: Session, record: schemas.DeliveryRecordCreate):
    while True:
        code = f"{random.randint(0, 999999):06d}"
        
        # Check if this code is already in use for a 'WAITING' order
        existing = db.query(models.deliveryRecords).filter(
            models.deliveryRecords.confirmation_code == code,
            models.deliveryRecords.status == "WAITING"
        ).first()
        
        if not existing:
            break
    
    new_record_data = record.model_dump()
    new_record_data['confirmation_code'] = code
    
    new_record = models.deliveryRecords(**new_record_data)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

def update_delivery_record_by_robotID(db: Session, record_id: int, video_url: str):
    record = db.query(models.deliveryRecords).filter(models.deliveryRecords.id == record_id).first()
    
    if not record:
        return None  
    
    record.videourl = video_url
    record.last_updated_at = datetime.utcnow()

    db.commit()
    db.refresh(record)
    return record

def update_delivery_record_after_stop_record(db: Session, text2find: str, video_url: str):
    
    record = db.query(models.deliveryRecords).filter(models.deliveryRecords.videourl == text2find).first()
    
    if not record:
        return None  
    
    record.videourl = video_url
    record.last_updated_at = datetime.utcnow()

    db.commit()
    db.refresh(record)
    return record

def update_Statisfication_after_stop_record(db: Session, statisfication: str, video_url: str):
    
    record = db.query(models.deliveryRecords).filter(models.deliveryRecords.videourl == video_url).first()
    
    if not record:
        return None  
    
    record.statisfied_level = statisfication
    record.last_updated_at = datetime.utcnow()

    db.commit()
    db.refresh(record)
    return record

def get_robots_count(db: Session) -> int:
    """Returns the total number of robots in the database."""
    return db.query(models.Robot).count()
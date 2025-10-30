from sqlalchemy.orm import Session
from app import models, schemas

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
    new_item = models.InventoryItem(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

def create_log(db: Session, log: schemas.RobotLogCreate):
    new_log = models.RobotLog(**log.model_dump())
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

def create_delivery_record(db: Session, record: schemas.RobotLogCreate):
    new_record = models.deliveryRecords(**record.model_dump())
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

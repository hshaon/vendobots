# app/routers/logs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
# Import models
from app import crud, schemas, database, models

router = APIRouter(prefix="/deliveryRecord", tags=["deliveryRecord"])

@router.get("/", response_model=list[schemas.DeliveryRecord])
def get_delivery_record(db: Session = Depends(database.get_db)):
    return db.query(models.deliveryRecords).all()

@router.post("/", response_model=schemas.DeliveryRecord)
def create_delivery_record(record: schemas.DeliveryRecordCreate, db: Session = Depends(database.get_db)):
    return crud.create_delivery_record(db, record)

@router.get("/{robot_id}", response_model=list[schemas.DeliveryRecord])
def get_delivery_record_by_robotID(robot_id: int, db: Session = Depends(database.get_db)):
    records = db.query(models.deliveryRecords).filter(models.deliveryRecords.robot_id == robot_id).all()
    return records

@router.post("/{record_id}")
def update_delivery_record_by_robotID(record_id: int, body: dict, db: Session = Depends(database.get_db)):
    video_url = body.get("video_url")
    print(video_url)
    if not video_url:
        raise HTTPException(status_code=400, detail="Missing 'video_url' in request body")

    updated_record = crud.update_delivery_record_by_robotID(db, record_id, video_url)

    return updated_record

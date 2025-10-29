# app/routers/logs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
# Import models
from app import crud, schemas, database, models

router = APIRouter(prefix="/deliveryRecord", tags=["deliveryRecord"])

@router.get("/", response_model=list[schemas.DeliveryRecord])
def get_logs(db: Session = Depends(database.get_db)):
    print("vo")
    return db.query(models.deliveryRecords).all()


@router.post("/", response_model=schemas.DeliveryRecord)
def create_delivery_record(record: schemas.DeliveryRecordCreate, db: Session = Depends(database.get_db)):
    print("go")
    return crud.create_delivery_record(db, record)
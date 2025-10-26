# app/routers/logs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
# Import models
from app import crud, schemas, database, models

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/", response_model=list[schemas.RobotLog])
def get_logs(db: Session = Depends(database.get_db)):
    # This was the bug:
    # return db.query(schemas.RobotLog).all()  
    
    # This is the fix (query models.RobotLog):
    return db.query(models.RobotLog).all()


@router.post("/", response_model=schemas.RobotLog)
def create_log(log: schemas.RobotLogCreate, db: Session = Depends(database.get_db)):
    return crud.create_log(db, log)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import crud, schemas, database

router = APIRouter(prefix="/robots", tags=["robots"])

@router.get("/", response_model=list[schemas.Robot])
def get_all_robots(db: Session = Depends(database.get_db)):
    return crud.get_robots(db)

@router.post("/", response_model=schemas.Robot)
def create_robot(robot: schemas.RobotCreate, db: Session = Depends(database.get_db)):
    return crud.create_robot(db, robot)

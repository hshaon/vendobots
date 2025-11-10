from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app import crud, schemas, database, models
from fastapi import HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/robots", tags=["robots"])

@router.get("/", response_model=list[schemas.Robot])
def get_all_robots(db: Session = Depends(database.get_db)):
    return crud.get_robots(db)

@router.post("/", response_model=schemas.Robot)
def create_robot(robot: schemas.RobotCreate, db: Session = Depends(database.get_db)):
    return crud.create_robot(db, robot)

@router.get("/{robot_id}", response_model=schemas.Robot)
def get_robot_by_id(robot_id: int, db: Session = Depends(database.get_db)):
    print("✅ Received robot_id:", robot_id)
    allRobots = crud.get_robots(db)

    for robot in allRobots:
        if robot.id == robot_id:
            # Return this single robot, not the whole list
            return robot

    # If no match found, return 404
    raise HTTPException(status_code=404, detail="Robot not found")

class RobotPositionUpdate(BaseModel):
    current_pos_x: float
    current_pos_y: float

@router.put("/{robot_id}/position", response_model=schemas.Robot)
def update_robot_position(
    robot_id: int, 
    position: RobotPositionUpdate, 
    db: Session = Depends(database.get_db)
):
    db_robot = db.query(models.Robot).filter(models.Robot.id == robot_id).first()
    if not db_robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    db_robot.current_pos_x = position.current_pos_x
    db_robot.current_pos_y = position.current_pos_y
    db_robot.last_updated = func.now()
    
    db.commit()
    db.refresh(db_robot)
    return db_robot
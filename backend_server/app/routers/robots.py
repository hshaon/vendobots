from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import crud, schemas, database
from fastapi import HTTPException

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

@router.put("/{robot_id}/location", response_model=schemas.Robot)
def update_robot_location_endpoint(
    robot_id: int, 
    location: schemas.RobotLocationUpdate, 
    db: Session = Depends(database.get_db)
):
    """Updates the current x/y location of a robot."""
    updated_robot = crud.update_robot_location(db, robot_id, location)
    if updated_robot is None:
        raise HTTPException(status_code=404, detail="Robot not found")
    return updated_robot
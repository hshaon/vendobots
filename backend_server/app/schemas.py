from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class InventoryItemBase(BaseModel):
    name: str
    image_url: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = 0

class InventoryItemCreate(InventoryItemBase):
    robot_id: Optional[int] = None

class InventoryItem(InventoryItemBase):
    id: int
    robot_id: Optional[int]
    class Config:
        from_attributes = True

class RobotBase(BaseModel):
    name: str
    image_url: Optional[str] = None
    status: Optional[str] = "idle"
    battery_level: Optional[int] = 100

class RobotCreate(RobotBase):
    pass

class Robot(RobotBase):
    id: int
    last_updated: datetime
    inventory_items: List[InventoryItem] = []
    class Config:
        from_attributes = True

class RobotLogBase(BaseModel):
    message: str
    robot_id: int

class RobotLogCreate(RobotLogBase):
    pass

class RobotLog(RobotLogBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

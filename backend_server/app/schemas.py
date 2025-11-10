from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class InventoryItemBase(BaseModel):
    name: str
    image_url: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = 0
    category: Optional[str] = None

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
    current_pos_x: Optional[float] = 0.0
    current_pos_y: Optional[float] = 0.0

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


class DeliveryRecordBase(BaseModel):
    message: str
    robot_id: int
    
    address: str
    videourl: Optional[str] = None
    inventory_ids: str
    quantity: str
    status: str
    
    start_pos_x: Optional[float] = None
    start_pos_y: Optional[float] = None
    dest_pos_x: Optional[float] = None
    dest_pos_y: Optional[float] = None

class DeliveryRecordCreate(DeliveryRecordBase):
    pass

class DeliveryRecord(DeliveryRecordBase):
    id: int
    created_at: datetime
    last_updated_at: datetime
    class Config:
        from_attributes = True
        
class ControlCommand(BaseModel):
    robot_id: int
    command: str  # e.g., "forward", "backward", "left", "right", "stop"

class ControlResponse(BaseModel):
    status: str
    message: str
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DECIMAL, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Robot(Base):
    __tablename__ = "robots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    image_url = Column(Text)
    status = Column(String(50), default="idle")
    battery_level = Column(Integer, default=100)
    last_updated = Column(TIMESTAMP, server_default=func.now())
    
    current_pos_x = Column(DECIMAL(10, 4), default=0.0)
    current_pos_y = Column(DECIMAL(10, 4), default=0.0)

    inventory_items = relationship("InventoryItem", back_populates="robot")
    logs = relationship("RobotLog", back_populates="robot")

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    image_url = Column(Text)
    price = Column(DECIMAL(10, 2))
    quantity = Column(Integer, default=0)
    category = Column(Text)
    robot_id = Column(Integer, ForeignKey("robots.id", ondelete="SET NULL"))

    robot = relationship("Robot", back_populates="inventory_items")

class RobotLog(Base):
    __tablename__ = "robot_logs"

    id = Column(Integer, primary_key=True, index=True)
    robot_id = Column(Integer, ForeignKey("robots.id"))
    message = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    robot = relationship("Robot", back_populates="logs")


class deliveryRecords(Base):
    __tablename__ = "delivery_records"

    id = Column(Integer, primary_key=True, index=True)
    robot_id = Column(Integer, ForeignKey("robots.id"))
    # robot = relationship("Robot", back_populates="logs")
    message = Column(Text)
    videourl = Column(Text)
    address = Column(Text)
    inventory_ids = Column(Text)
    quantity = Column(Text)
    status = Column(Text) #DELIVERIED, CANCELED, WAITING,
    
    start_pos_x = Column(DECIMAL(10, 4), nullable=True)
    start_pos_y = Column(DECIMAL(10, 4), nullable=True)
    dest_pos_x = Column(DECIMAL(10, 4), nullable=True)
    dest_pos_y = Column(DECIMAL(10, 4), nullable=True)
    
    confirmation_code = Column(String(6), nullable=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_updated_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('robot_id', 'confirmation_code', 'status', name='_robot_code_status_uc'),
    )
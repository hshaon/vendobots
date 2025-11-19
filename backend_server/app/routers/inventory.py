# app/routers/inventory.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas, database

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("/", response_model=list[schemas.InventoryItem])
def get_inventory_items(db: Session = Depends(database.get_db)):
    return crud.get_inventory(db)

@router.post("/", response_model=schemas.InventoryItem)
def create_inventory_item(item: schemas.InventoryItemCreate, db: Session = Depends(database.get_db)):
    return crud.create_inventory_item(db, item)

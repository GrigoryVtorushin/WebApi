from typing import List

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

import schemas
from database import get_db
from sqlalchemy.orm import Session
from crud import (
    create_category, get_categories, get_category, update_category, delete_category,
    create_product, get_products, get_product, update_product, delete_product
)

router_websocket = APIRouter()
router_categories = APIRouter(prefix='/categories', tags=['category'])
router_products = APIRouter(prefix='/products', tags=['product'])


# WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)


    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


async def notify_clients(message: str):
    for connection in manager.active_connections:
        await connection.send_text(message)


@router_websocket.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    await manager.broadcast(f"Пользователь #{client_id} присоединился к чату.")
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Пользователь #{client_id} написал: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Пользователь #{client_id} покинул чат")


# Категории
@router_categories.post("/", response_model=schemas.Category)
async def create_category_route(category_data: schemas.CategoryCreate, db: Session = Depends(get_db)):
    category = create_category(db, category_data)
    await notify_clients(f"Category added: {category.name}")
    return category


@router_categories.get("/", response_model=List[schemas.Category])
async def read_categories(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    categories = get_categories(db, skip=skip, limit=limit)
    return categories


@router_categories.get("/{category_id}", response_model=schemas.Category)
async def read_category(category_id: int, db: Session = Depends(get_db)):
    category = get_category(db, category_id)
    return category


@router_categories.patch("/{category_id}", response_model=schemas.Category)
async def update_category_route(category_id: int, category_data: schemas.CategoryUpdate, db: Session = Depends(get_db)):
    updated_category = update_category(db, category_id, category_data)
    if updated_category:
        await notify_clients(f"Category updated: {updated_category.name}")
        return updated_category
    return {"message": "Category not found"}


@router_categories.delete("/{category_id}")
async def delete_category_route(category_id: int, db: Session = Depends(get_db)):
    deleted = delete_category(db, category_id)
    if deleted:
        await notify_clients(f"Category deleted: ID {category_id}")
        return {"message": "Category deleted"}
    return {"message": "Category not found"}


# Products
@router_products.post("/", response_model=schemas.Item)
async def create_product_route(schema: schemas.ItemCreate, db: Session = Depends(get_db)):
    product = create_product(db, schema)
    await notify_clients(f"Item added: {product.name}")
    return product


@router_products.get("/", response_model=List[schemas.Item])
async def read_products(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    products = get_products(db, skip=skip, limit=limit)
    return products


@router_products.get("/{item_id}", response_model=schemas.Item)
async def read_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product(db, product_id)
    return product


@router_products.patch("/{item_id}")
async def update_product_route(product_id: int, schema: schemas.ItemUpdate, db: Session = Depends(get_db)):
    updated_product = update_product(db, product_id, schema)
    if updated_product:
        await notify_clients(f"Item updated: {updated_product.name}")
        return updated_product
    return {"message": "Item not found"}


@router_products.delete("/{item_id}")
async def delete_product_route(product_id: int, db: Session = Depends(get_db)):
    deleted = delete_product(db, product_id)
    if deleted:
        await notify_clients(f"Item deleted: ID {product_id}")
        return {"message": "Item deleted"}
    return {"message": "Item not found"}

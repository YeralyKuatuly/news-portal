from fastapi import FastAPI, Depends, HTTPException, Header, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from faker import Faker
import random
import json
import asyncio
from datetime import timedelta
from typing import List

from .database import get_db, init_db
from .models import News
from .auth import (
    authenticate_admin, 
    create_access_token, 
    verify_admin_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

app = FastAPI(title="News Portal API")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        if self.active_connections:
            # Send to all connected clients
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Инициализация БД
@app.on_event("startup")
def startup_event():
    init_db()

# Faker для генерации новостей
fake = Faker('ru_RU')

# === PUBLIC ENDPOINTS ===

@app.get("/")
def root():
    return {"message": "News Portal API", "docs": "/docs"}

@app.get("/news")
def get_news(db: Session = Depends(get_db)):
    """Получить все новости (отсортированы по дате)"""
    news = db.query(News).order_by(News.created_at.desc()).all()
    return [n.to_dict() for n in news]

@app.get("/news/{news_id}")
def get_news_by_id(news_id: int, db: Session = Depends(get_db)):
    """Получить конкретную новость"""
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news.to_dict()

# === WEBSOCKET ENDPOINT ===

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time news updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # For now, we just echo back (can be extended for client commands)
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# === AUTHENTICATION ENDPOINTS ===

@app.post("/admin/login")
def login(username: str = Form(...), password: str = Form(...)):
    """
    Admin login endpoint
    
    Returns JWT token for authenticated admin
    """
    if not authenticate_admin(username, password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

# === ADMIN ENDPOINTS ===

@app.post("/admin/news/generate")
async def generate_news(
    count: int = 1,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token)
):
    """
    Генерировать случайные новости
    
    Requires: Bearer token in Authorization header
    Query param: count (сколько новостей создать)
    """
    generated = []
    
    for _ in range(count):
        news = News(
            title=fake.sentence(nb_words=6),
            content=fake.text(max_nb_chars=300)
        )
        db.add(news)
        db.commit()
        db.refresh(news)
        generated.append(news.to_dict())
    
    # Broadcast new news to all WebSocket clients
    await manager.broadcast(json.dumps({
        "type": "new_news",
        "news": generated,
        "count": len(generated)
    }))
    
    return {
        "status": "success",
        "generated": len(generated),
        "news": generated
    }

@app.delete("/admin/news/{news_id}")
async def delete_news(
    news_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token)
):
    """Удалить новость (админ)"""
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    db.delete(news)
    db.commit()
    
    # Broadcast news deletion to all WebSocket clients
    await manager.broadcast(json.dumps({
        "type": "news_deleted",
        "news_id": news_id
    }))
    
    return {"status": "deleted", "id": news_id}

@app.delete("/admin/news")
async def clear_all_news(
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token)
):
    """Очистить все новости (админ)"""
    db.query(News).delete()
    db.commit()
    
    # Broadcast news clearing to all WebSocket clients
    await manager.broadcast(json.dumps({
        "type": "all_news_deleted"
    }))
    
    return {"status": "all news deleted"}

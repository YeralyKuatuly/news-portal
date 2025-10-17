from fastapi import FastAPI, Depends, HTTPException, Header, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from faker import Faker
import random
from datetime import timedelta
import time

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

# Simple in-memory cache for production optimization
news_cache = {
    "data": None,
    "timestamp": 0,
    "ttl": 30  # Cache for 30 seconds
}

def get_cached_news():
    """Get cached news if still valid, otherwise return None"""
    current_time = time.time()
    if (news_cache["data"] is not None and 
        current_time - news_cache["timestamp"] < news_cache["ttl"]):
        return news_cache["data"]
    return None

def set_cached_news(data):
    """Cache news data with timestamp"""
    news_cache["data"] = data
    news_cache["timestamp"] = time.time()

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
    """Получить все новости (отсортированы по дате) с кешированием"""
    # Check cache first
    cached_news = get_cached_news()
    if cached_news is not None:
        return cached_news
    
    # If not cached, fetch from database
    news = db.query(News).order_by(News.created_at.desc()).all()
    news_data = [n.to_dict() for n in news]
    
    # Cache the result
    set_cached_news(news_data)
    
    return news_data

@app.get("/news/{news_id}")
def get_news_by_id(news_id: int, db: Session = Depends(get_db)):
    """Получить конкретную новость"""
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news.to_dict()

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
def generate_news(
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
    
    # Invalidate cache when news is added
    news_cache["data"] = None
    news_cache["timestamp"] = 0
    
    return {
        "status": "success",
        "generated": len(generated),
        "news": generated
    }

@app.delete("/admin/news/{news_id}")
def delete_news(
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
    
    # Invalidate cache when news is deleted
    news_cache["data"] = None
    news_cache["timestamp"] = 0
    
    return {"status": "deleted", "id": news_id}

@app.delete("/admin/news")
def clear_all_news(
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token)
):
    """Очистить все новости (админ)"""
    db.query(News).delete()
    db.commit()
    
    # Invalidate cache when all news is deleted
    news_cache["data"] = None
    news_cache["timestamp"] = 0
    
    return {"status": "all news deleted"}

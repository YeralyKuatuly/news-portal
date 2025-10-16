from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from faker import Faker
import random

from .database import get_db, init_db
from .models import News

app = FastAPI(title="News Portal API")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация БД
@app.on_event("startup")
def startup_event():
    init_db()

# Faker для генерации новостей
fake = Faker('ru_RU')

# Секретный токен для админа
ADMIN_TOKEN = "secret_admin_token_12345"

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

# === ADMIN ENDPOINTS ===

def verify_admin_token(x_admin_token: str = Header(None)):
    """Проверка админского токена"""
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return True

@app.post("/admin/news/generate")
def generate_news(
    count: int = 1,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    """
    Генерировать случайные новости
    
    Header: X-Admin-Token: secret_admin_token_12345
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
    
    return {
        "status": "success",
        "generated": len(generated),
        "news": generated
    }

@app.delete("/admin/news/{news_id}")
def delete_news(
    news_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    """Удалить новость (админ)"""
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    db.delete(news)
    db.commit()
    return {"status": "deleted", "id": news_id}

@app.delete("/admin/news")
def clear_all_news(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    """Очистить все новости (админ)"""
    db.query(News).delete()
    db.commit()
    return {"status": "all news deleted"}

# 📰 Новостной Портал MVP

Тестовое задание: новостной портал с автообновлением.

## Технологии

- **Backend**: FastAPI + SQLite + SQLAlchemy
- **Frontend**: React (CDN) + Tailwind CSS
- **Deploy**: Docker + Docker Compose

## Функционал

✅ Главная страница со списком новостей  
✅ Автообновление каждые 5 секунд БЕЗ перезагрузки  
✅ Админ-панель для генерации новостей  
✅ REST API с документацией  

## Запуск проекта

### Быстрый старт
```bash
# Клонировать/скачать проект
cd news-portal

# Запустить в Docker
docker-compose up --build
```

Откроется:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Использование

1. Открой http://localhost:3000
2. Нажми "Админ панель"
3. Сгенерируй несколько новостей
4. Новости появятся автоматически (без перезагрузки!)

## API Endpoints

### Public
- `GET /news` - Получить все новости
- `GET /news/{id}` - Получить новость по ID

### Admin (требуется заголовок `X-Admin-Token: secret_admin_token_12345`)
- `POST /admin/news/generate?count=5` - Сгенерировать новости
- `DELETE /admin/news/{id}` - Удалить новость
- `DELETE /admin/news` - Очистить все новости

## Структура проекта
news-portal/
├── backend/          # FastAPI приложение
├── frontend/         # React интерфейс
└── docker-compose.yml

## Разработка
```bash
# Backend отдельно
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend отдельно
cd frontend
python -m http.server 3000
```
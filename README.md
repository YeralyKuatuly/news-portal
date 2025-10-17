# 📰 Новостной Портал

Современный новостной портал с JWT аутентификацией, WebSocket real-time обновлениями и админ-панелью.


## ✨ Функционал

✅ **Публичная часть**: Просмотр новостей с real-time обновлениями  
✅ **WebSocket Real-time**: Мгновенные обновления без перезагрузки  
✅ **JWT Аутентификация**: Безопасный вход в админ-панель  
✅ **Админ-панель**: Генерация, удаление и управление новостями  
✅ **REST API**: Полная документация Swagger  

## 🏃‍♂️ Быстрый запуск

```bash
# Клонировать проект
git clone <repository-url>
cd news-portal

# Запустить все сервисы
docker-compose up --build
```

**Доступные URL:**
- 🌐 **Сайт**: http://localhost:3000
- 🔧 **API**: http://localhost:8000
- 📚 **Документация**: http://localhost:8000/docs

## 🔐 Админ-доступ

**Тестовые данные:**
- **Логин**: `admin`
- **Пароль**: `admin123`

1. Откройте http://localhost:3000
2. Нажмите "Админ панель"
3. Войдите с тестовыми данными
4. Управляйте новостями через удобный интерфейс

## 📡 API Endpoints

### Публичные
- `GET /news` - Получить все новости
- `GET /news/{id}` - Получить новость по ID

### WebSocket
- `WS /ws` - Real-time подключение для мгновенных обновлений

### Аутентификация
- `POST /admin/login` - Вход в админ-панель (username, password)

### Админ (требуется JWT Bearer token)
- `POST /admin/news/generate?count=5` - Сгенерировать новости
- `DELETE /admin/news/{id}` - Удалить новость
- `DELETE /admin/news` - Очистить все новости

## 🏗️ Структура проекта

```
news-portal/
├── backend/
│   ├── app/
│   │   ├── main.py      # FastAPI приложение
│   │   ├── auth.py      # JWT аутентификация
│   │   ├── models.py    # SQLAlchemy модели
│   │   └── database.py  # База данных
│   ├── requirements.txt # Python зависимости
│   └── Dockerfile
├── frontend/
│   ├── index.html       # Главная страница
│   ├── admin.html       # Админ-панель
│   └── Dockerfile
└── docker-compose.yml   # Оркестрация сервисов
```

## 🛠️ Разработка

### Backend (отдельно)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (отдельно)
```bash
cd frontend
python -m http.server 3000
```

## 🔒 Безопасность

- **JWT токены** с истечением через 30 минут
- **bcrypt** для хеширования паролей
- **CORS** настроен для dev
- **Bearer token** аутентификация для API

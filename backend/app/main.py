from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from app.models import Category
from app.routers import transactions, categories, budgets, insights, chat, goals # <-- Добавили goals

# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI(title="WealthWise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def seed_db():
    db = SessionLocal()
    if db.query(Category).count() == 0:
        default_categories = [
            {"name": "Продукты", "type": "expense", "keywords": ["пятерочка", "магнит", "перекресток", "spar", "магазин", "food"]},
            {"name": "Транспорт", "type": "expense", "keywords": ["uber", "yandex", "taxi", "бензин", "азс", "metro", "transport"]},
            {"name": "Кафе и рестораны", "type": "expense", "keywords": ["kfc", "mcdonalds", "burger", "ресторан", "cafe"]},
            {"name": "Зарплата", "type": "income", "keywords": ["salary", "зарплата", "аванс", "выплата"]},
            {"name": "Переводы", "type": "expense", "keywords": ["tinkoff", "sberbank", "перевод", "transfer"]},
            {"name": "Дом и ремонт", "type": "expense", "keywords": ["leroy", "merlin", "икеа", "жкх", "аренда"]},
            {"name": "Развлечения", "type": "expense", "keywords": ["кино", "steam", "games", "netflix"]},
        ]
        for cat in default_categories:
            db_cat = Category(
                name=cat["name"],
                type=cat["type"],
                keywords=cat["keywords"]
            )
            db.add(db_cat)
        db.commit()
    db.close()

seed_db()

app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(budgets.router)
app.include_router(insights.router)
app.include_router(chat.router)
app.include_router(goals.router) # <-- Подключаем

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
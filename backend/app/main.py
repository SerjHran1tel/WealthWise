from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import logging

from  backend.app.database import engine, Base
from backend.app.routers import transactions, categories, budgets, goals, insights, chat, reports, profile
from backend.app.services.scheduler import start_scheduler, stop_scheduler

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WealthWise AI - Advanced Financial Assistant",
    description="AI-powered personal finance manager with personalization and predictive analytics",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(budgets.router)
app.include_router(goals.router)
app.include_router(insights.router)
app.include_router(chat.router)
app.include_router(reports.router)
app.include_router(profile.router)  # 🔥 NEW: User profile for personalization

# Static files (frontend)
try:
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialization on startup"""
    logger.info("🚀 Starting WealthWise AI v2.0 - Advanced Financial Assistant")

    # Initialize default categories if needed
    from backend.app.database import SessionLocal
    from backend.app.models import Category

    db = SessionLocal()
    try:
        # Полный список категорий с корректными ключевыми словами
        all_categories = [
            Category(name="Продукты", type="expense", icon="🛒",
                     keywords=["продукт", "супермаркет", "пятёрочка", "пятерочка", "магнит",
                               "перекрёсток", "вкусвилл", "лента", "ашан", "дикси", "гастроном"]),
            Category(name="Транспорт", type="expense", icon="🚗",
                     keywords=["такси", "uber", "метро", "транспорт", "бензин", "каршеринг",
                               "автобус", "электричка", "аэрофлот", "ржд", "авиабилет", "парковка"]),
            Category(name="Развлечения", type="expense", icon="🎬",
                     keywords=["кино", "развлечение", "игры", "spotify", "netflix", "youtube premium",
                               "театр", "музей", "концерт", "билет"]),
            Category(name="Здоровье", type="expense", icon="💊",
                     keywords=["аптека", "врач", "лекарство", "медицина", "больница",
                               "клиника", "стоматолог", "анализ"]),
            Category(name="Одежда", type="expense", icon="👕",
                     keywords=["одежда", "обувь", "zara", "h&m", "унiqlo", "lacoste"]),
            Category(name="Кафе и рестораны", type="expense", icon="☕",
                     keywords=["кафе", "ресторан", "доставка еды", "макдоналдс", "kfc", "бургер",
                               "пицца", "суши", "фастфуд", "столовая"]),
            Category(name="Красота", type="expense", icon="💅",
                     keywords=["парикмахер", "стрижка", "маникюр", "педикюр", "косметика",
                               "салон красоты", "химчистка", "spa", "спа"]),
            Category(name="Спорт", type="expense", icon="🏋️",
                     keywords=["спортзал", "фитнес", "бассейн", "тренажёр", "спорттовары",
                               "абонемент", "йога", "секция"]),
            Category(name="ЖКХ и связь", type="expense", icon="🏠",
                     keywords=["коммунальные", "жкх", "квартплата", "электричество", "газ",
                               "вода", "интернет", "телефон", "мобильная связь", "пополнение"]),
            Category(name="Путешествия", type="expense", icon="✈️",
                     keywords=["отель", "гостиница", "хостел", "airbnb", "экскурсия",
                               "тур", "виза", "страховка"]),
            Category(name="Зарплата", type="income", icon="💰",
                     keywords=["зарплата", "salary", "аванс", "премия", "оклад"]),
            Category(name="Прочее", type="expense", icon="📦", keywords=[]),
        ]

        existing_names = {c.name for c in db.query(Category.name).all()}
        created = 0

        if not existing_names:
            # Первый запуск — создаём все
            db.add_all(all_categories)
            db.commit()
            created = len(all_categories)
            logger.info(f"✅ Created {created} default categories")
        else:
            # Добавляем только отсутствующие + обновляем ключевые слова существующих
            for cat_def in all_categories:
                if cat_def.name not in existing_names:
                    db.add(cat_def)
                    created += 1
                    logger.info(f"   ➕ Added missing category: {cat_def.name}")
                else:
                    # Обновляем keywords для существующих (убираем "магазин" и др. проблемные слова)
                    existing = db.query(Category).filter(Category.name == cat_def.name).first()
                    if existing and cat_def.keywords:
                        existing.keywords = cat_def.keywords
            if created > 0:
                db.commit()
                logger.info(f"✅ Added {created} new categories")

            total = db.query(Category).count()
            logger.info(f"✅ Found {total} categories total")
    except Exception as e:
        logger.error(f"❌ Error initializing categories: {e}")
        db.rollback()
    finally:
        db.close()

    logger.info("✅ Database initialized")

    # 🔥 START SCHEDULER
    logger.info("")
    logger.info("⏰ Starting automated tasks...")
    try:
        start_scheduler()
        logger.info("✅ Scheduler started: Weekly reports + Daily analytics")
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")

    logger.info("")
    logger.info("🧠 Advanced AI agents ready:")
    logger.info("   - Personalized Chat Agent (adapts to user personality)")
    logger.info("   - Predictive Analytics Agent (forecasts & anomalies)")
    logger.info("   - User Profiler (learns financial behavior)")
    logger.info("   - RAG Classifier (smart categorization)")
    logger.info("")
    logger.info("🔒 Privacy: All data processed locally via Ollama")
    logger.info("📊 API Documentation: http://localhost:8000/docs")
    logger.info("💬 Chat Health Check: http://localhost:8000/api/chat/health")
    logger.info("👤 User Profile: http://localhost:8000/api/profile/")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down WealthWise AI...")

    # Stop scheduler
    try:
        stop_scheduler()
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


@app.get("/")
async def root():
    """Main page - serve frontend"""
    try:
        return FileResponse("frontend/index.html")
    except Exception:
        return {
            "message": "WealthWise AI v2.0 is running",
            "features": [
                "Personalized AI Financial Psychologist",
                "Predictive Analytics & Forecasting",
                "Behavioral Pattern Recognition",
                "Smart Budget Management",
                "Goal Tracking & Feasibility Analysis",
                "100% Local Processing (Privacy First)"
            ],
            "docs": "/docs",
            "health": "/health"
        }


@app.get("/health")
async def health_check():
    """API health check"""
    from backend.app.services.ollama_client import ollama_client

    try:
        ollama_available = await ollama_client.check_health()
        ollama_status = "available" if ollama_available else "unavailable"
    except:
        ollama_status = "unavailable"

    return {
        "status": "healthy",
        "service": "WealthWise AI",
        "version": "2.0.0",
        "ollama_status": ollama_status,
        "features": {
            "personalization": True,
            "predictive_analytics": True,
            "behavioral_analysis": True,
            "local_processing": True
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
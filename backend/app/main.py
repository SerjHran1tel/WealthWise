from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import logging

from app.database import engine, Base
from app.routers import transactions, categories, budgets, goals, insights, chat, reports, profile

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
    from app.database import SessionLocal
    from app.models import Category

    db = SessionLocal()
    try:
        # Check if categories exist
        count = db.query(Category).count()
        if count == 0:
            logger.info("📦 Initializing default categories...")
            default_categories = [
                Category(name="Продукты", type="expense", icon="🛒",
                         keywords=["продукт", "магазин", "супермаркет", "пятерочка", "магнит", "перекрёсток"]),
                Category(name="Транспорт", type="expense", icon="🚗",
                         keywords=["такси", "uber", "яндекс", "метро", "транспорт", "бензин", "каршеринг"]),
                Category(name="Развлечения", type="expense", icon="🎬",
                         keywords=["кино", "развлечение", "игры", "spotify", "подписка"]),
                Category(name="Здоровье", type="expense", icon="💊",
                         keywords=["аптека", "врач", "лекарство", "медицина", "больница"]),
                Category(name="Одежда", type="expense", icon="👕",
                         keywords=["одежда", "обувь", "магазин одежды", "zara", "h&m"]),
                Category(name="Кафе и рестораны", type="expense", icon="☕",
                         keywords=["кафе", "ресторан", "еда", "доставка", "макдональдс", "кфс"]),
                Category(name="Зарплата", type="income", icon="💰",
                         keywords=["зарплата", "salary", "аванс", "премия"]),
                Category(name="Прочее", type="expense", icon="📦", keywords=[]),
            ]
            db.add_all(default_categories)
            db.commit()
            logger.info(f"✅ Created {len(default_categories)} default categories")
        else:
            logger.info(f"✅ Found {count} existing categories")
    except Exception as e:
        logger.error(f"❌ Error initializing categories: {e}")
        db.rollback()
    finally:
        db.close()

    logger.info("✅ Database initialized")
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
    from app.services.ollama_client import ollama_client

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
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
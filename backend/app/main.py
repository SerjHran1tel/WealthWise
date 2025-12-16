from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import logging

from app.database import engine, Base
from app.routers import transactions, categories, budgets, goals, insights, chat, reports

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WealthWise API",
    description="AI-powered personal finance manager",
    version="1.0.0"
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

# Static files (frontend)
try:
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialization on startup"""
    logger.info("Starting WealthWise application...")

    # Initialize default categories if needed
    from app.database import SessionLocal
    from app.models import Category

    db = SessionLocal()
    try:
        # Check if categories exist
        count = db.query(Category).count()
        if count == 0:
            logger.info("Initializing default categories...")
            default_categories = [
                Category(name="Продукты", type="expense", icon="🛒",
                         keywords=["продукт", "магазин", "супермаркет", "пятерочка", "магнит"]),
                Category(name="Транспорт", type="expense", icon="🚗",
                         keywords=["такси", "uber", "яндекс", "метро", "транспорт"]),
                Category(name="Развлечения", type="expense", icon="🎬",
                         keywords=["кино", "развлечение", "игры", "spotify"]),
                Category(name="Здоровье", type="expense", icon="💊",
                         keywords=["аптека", "врач", "лекарство", "медицина"]),
                Category(name="Одежда", type="expense", icon="👕",
                         keywords=["одежда", "обувь", "магазин одежды"]),
                Category(name="Зарплата", type="income", icon="💰",
                         keywords=["зарплата", "salary", "аванс"]),
                Category(name="Прочее", type="expense", icon="📦", keywords=[]),
            ]
            db.add_all(default_categories)
            db.commit()
            logger.info(f"Created {len(default_categories)} default categories")
    except Exception as e:
        logger.error(f"Error initializing categories: {e}")
        db.rollback()
    finally:
        db.close()

    logger.info("Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down WealthWise...")


@app.get("/")
async def root():
    """Main page - serve frontend"""
    try:
        return FileResponse("frontend/index.html")
    except Exception:
        return {"message": "WealthWise API is running", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "service": "WealthWise API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
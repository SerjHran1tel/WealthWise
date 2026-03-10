from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.app.core.config import settings

# Настройка SQLite
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} # Нужно только для SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# Dependency для FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
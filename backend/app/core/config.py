import os
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "WealthWise MVP"
    DEBUG: bool = True

    # Пути
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DATABASE_URL: str = f"sqlite:///{DATA_DIR}/wealthwise.db"

    # Заглушки для ML путей (понадобятся позже)
    EMBEDDING_MODEL_PATH: str = str(BASE_DIR / "models/embeddings/")
    CLASSIFIER_MODEL_PATH: str = str(BASE_DIR / "models/classifier/")

    class Config:
        env_file = ".env"


settings = Settings()

# Создаем папку data если нет
os.makedirs(settings.DATA_DIR, exist_ok=True)
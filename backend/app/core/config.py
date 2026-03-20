import os
from pydantic_settings import BaseSettings
from pathlib import Path
from zoneinfo import ZoneInfo


class Settings(BaseSettings):
    APP_NAME: str = "WealthWise MVP"
    DEBUG: bool = True

    # Простая авторизация для локального использования
    APP_PASSWORD: str = "wealthwise2024"  # Можно изменить в .env

    # ID пользователя по умолчанию (единая точка конфигурации)
    DEFAULT_USER_ID: str = "local_user_001"

    # Пути
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DATABASE_URL: str = f"sqlite:///{DATA_DIR}/wealthwise.db"

    # Timezone для пользователя (по умолчанию UTC+3 для России)
    USER_TIMEZONE: str = "Europe/Moscow"

    # Ollama настройки
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3.5:4b"
    OLLAMA_TIMEOUT: int = 300

    # Пагинация
    DEFAULT_PAGE_SIZE: int = 500
    MAX_PAGE_SIZE: int = 501

    # Лимиты для парсинга
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_TRANSACTIONS_PER_FILE: int = 5000

    # Финансовые ограничения
    MIN_AMOUNT: float = 0.01
    MAX_AMOUNT: float = 10_000_000.00
    DEFAULT_CURRENCY: str = "RUB"

    # ML пути (для будущего)
    EMBEDDING_MODEL_PATH: str = str(BASE_DIR / "models/embeddings/")
    CLASSIFIER_MODEL_PATH: str = str(BASE_DIR / "models/classifier/")

    class Config:
        env_file = ".env"

    @property
    def timezone(self) -> ZoneInfo:
        """Возвращает timezone объект"""
        return ZoneInfo(self.USER_TIMEZONE)


settings = Settings()

# Создаем необходимые папки
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.EMBEDDING_MODEL_PATH, exist_ok=True)
os.makedirs(settings.CLASSIFIER_MODEL_PATH, exist_ok=True)
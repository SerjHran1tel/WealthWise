from sqlalchemy.orm import Session
from app.models import Category
import re


class ClassifierAgent:
    def __init__(self):
        # TODO: Загрузка ML модели (pickle)
        # TODO: Инициализация ChromaDB client
        pass

    def categorize(self, db: Session, description: str, amount: float) -> str:
        """
        Возвращает category_id.
        Логика:
        1. Ищем по ключевым словам (Rule-based)
        2. (TODO) Ищем в векторной базе (RAG)
        3. (TODO) Используем ML классификатор
        4. Если ничего не нашли -> возвращаем None (Uncategorized)
        """

        description_lower = description.lower()

        # Получаем все категории с ключевыми словами
        # В продакшене это нужно кешировать, а не дергать БД каждый раз
        categories = db.query(Category).all()

        for cat in categories:
            if not cat.keywords:
                continue

            # Простая проверка вхождения ключевых слов
            for keyword in cat.keywords:
                if keyword.lower() in description_lower:
                    return cat.id

        # Если правило не сработало (TODO: тут должен быть вызов ML)
        return None


# Синглтон агента
classifier = ClassifierAgent()
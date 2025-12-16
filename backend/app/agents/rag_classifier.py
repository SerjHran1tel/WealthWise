from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Category, Transaction
from app.services.ollama_client import ollama_client
from typing import Optional, List, Dict
import logging
import json

logger = logging.getLogger(__name__)


class RAGClassifier:
    """
    RAG-based классификатор транзакций.
    Использует историю транзакций + семантический поиск + LLM для точной категоризации.
    """

    def __init__(self):
        self.cache = {}  # Кэш для частых описаний

    async def categorize_with_rag(
            self,
            db: Session,
            user_id: str,
            description: str,
            amount: float
    ) -> Optional[str]:
        """
        Категоризация транзакции с использованием RAG.

        Этапы:
        1. Проверка точного совпадения в истории (Adaptive Learning)
        2. Поиск похожих транзакций (Semantic Search)
        3. Анализ с помощью LLM (RAG)
        4. Fallback на правила
        """
        if not description:
            return None

        description_clean = description.strip().lower()

        # Проверка кэша
        if description_clean in self.cache:
            return self.cache[description_clean]

        # 1. ТОЧНОЕ СОВПАДЕНИЕ (быстрый путь)
        exact_match = self._find_exact_match(db, user_id, description_clean)
        if exact_match:
            self.cache[description_clean] = exact_match
            return exact_match

        # 2. ПОИСК ПОХОЖИХ ТРАНЗАКЦИЙ
        similar_transactions = self._find_similar_transactions(
            db, user_id, description_clean, limit=5
        )

        # 3. RAG: Используем LLM для категоризации на основе контекста
        category_id = await self._categorize_with_llm(
            db, description, amount, similar_transactions
        )

        if category_id:
            self.cache[description_clean] = category_id
            return category_id

        # 4. FALLBACK: Правила на основе ключевых слов
        return self._rule_based_categorization(db, description_clean)

    def _find_exact_match(
            self,
            db: Session,
            user_id: str,
            description: str
    ) -> Optional[str]:
        """Поиск точного совпадения в истории пользователя"""
        match = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            func.lower(Transaction.description) == description,
            Transaction.category_id.isnot(None)
        ).order_by(Transaction.date.desc()).first()

        return match.category_id if match else None

    def _find_similar_transactions(
            self,
            db: Session,
            user_id: str,
            description: str,
            limit: int = 5
    ) -> List[Dict]:
        """
        Поиск похожих транзакций (упрощённый семантический поиск).
        В идеале здесь использовать векторную БД (ChromaDB, Qdrant).
        """
        # Извлекаем ключевые слова из описания
        keywords = description.split()[:3]  # Первые 3 слова

        similar = []
        for keyword in keywords:
            results = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                func.lower(Transaction.description).like(f'%{keyword}%'),
                Transaction.category_id.isnot(None)
            ).limit(limit).all()

            for txn in results:
                if txn.category:
                    similar.append({
                        'description': txn.description,
                        'category': txn.category.name,
                        'amount': txn.amount
                    })

        return similar[:limit]

    async def _categorize_with_llm(
            self,
            db: Session,
            description: str,
            amount: float,
            similar_transactions: List[Dict]
    ) -> Optional[str]:
        """
        Категоризация с помощью LLM на основе похожих транзакций (RAG).
        """
        # Получаем все доступные категории
        categories = db.query(Category).filter(Category.type == "expense").all()
        category_list = [{"name": c.name, "keywords": c.keywords} for c in categories]

        # Формируем промпт с контекстом
        prompt = self._build_rag_prompt(
            description, amount, similar_transactions, category_list
        )

        try:
            # Запрашиваем категорию у LLM
            response = await ollama_client.generate(
                prompt=prompt,
                temperature=0.1,  # Низкая температура для детерминизма
                max_tokens=50
            )

            # Извлекаем название категории из ответа
            predicted_category = response.strip().strip('"').strip("'")

            # Находим категорию в БД
            category = db.query(Category).filter(
                func.lower(Category.name) == predicted_category.lower()
            ).first()

            if category:
                logger.info(f"RAG categorized '{description}' as '{category.name}'")
                return category.id

        except Exception as e:
            logger.error(f"LLM categorization error: {e}", exc_info=True)

        return None

    def _build_rag_prompt(
            self,
            description: str,
            amount: float,
            similar_transactions: List[Dict],
            categories: List[Dict]
    ) -> str:
        """Формирует промпт для LLM с контекстом (RAG)"""

        prompt_parts = [
            "Задача: определить категорию для финансовой транзакции.",
            "",
            f"ТРАНЗАКЦИЯ: {description}",
            f"СУММА: {amount:.2f} ₽",
            "",
            "ДОСТУПНЫЕ КАТЕГОРИИ:"
        ]

        for cat in categories:
            keywords = ", ".join(cat['keywords'][:5]) if cat['keywords'] else "нет"
            prompt_parts.append(f"- {cat['name']} (ключевые слова: {keywords})")

        if similar_transactions:
            prompt_parts.append("")
            prompt_parts.append("ПОХОЖИЕ ТРАНЗАКЦИИ ИЗ ИСТОРИИ:")
            for sim in similar_transactions[:3]:
                prompt_parts.append(
                    f"- '{sim['description']}' → категория '{sim['category']}'"
                )

        prompt_parts.extend([
            "",
            "ИНСТРУКЦИЯ:",
            "1. Проанализируй описание транзакции и сумму",
            "2. Сравни с похожими транзакциями из истории",
            "3. Выбери ОДНУ наиболее подходящую категорию из списка",
            "4. Ответь ТОЛЬКО названием категории, без дополнительных слов",
            "",
            "ОТВЕТ (только название категории):"
        ])

        return "\n".join(prompt_parts)

    def _rule_based_categorization(
            self,
            db: Session,
            description: str
    ) -> Optional[str]:
        """Fallback: категоризация по правилам (ключевые слова)"""
        categories = db.query(Category).all()

        for cat in categories:
            if not cat.keywords:
                continue

            for keyword in cat.keywords:
                if keyword.lower() in description:
                    logger.info(f"Rule-based match: '{description}' → '{cat.name}'")
                    return cat.id

        # Дополнительные жёсткие правила
        if any(word in description for word in ['uber', 'yandex', 'такси']):
            transport = next((c for c in categories if c.name == "Транспорт"), None)
            if transport:
                return transport.id

        if any(word in description for word in ['пятерочка', 'магнит', 'перекрёсток']):
            food = next((c for c in categories if c.name == "Продукты"), None)
            if food:
                return food.id

        return None


# Глобальный экземпляр RAG классификатора
rag_classifier = RAGClassifier()
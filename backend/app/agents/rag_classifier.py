from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models import Category, Transaction
from backend.app.services.ollama_client import ollama_client
from typing import Optional, List, Dict
import logging
import time

logger = logging.getLogger(__name__)

# TTL для кэша в секундах (30 минут)
CACHE_TTL = 1800
# Максимальный размер кэша
MAX_CACHE_SIZE = 5000


class RAGClassifier:
    """
    RAG-based классификатор транзакций.
    Использует историю транзакций + семантический поиск + LLM для точной категоризации.
    Включает TTL-кэш для описаний и кэш категорий из БД.
    """

    def __init__(self):
        # Кэш: description_clean -> (category_id, timestamp)
        self._description_cache: Dict[str, tuple] = {}
        # Кэш категорий из БД: [{"id": ..., "name": ..., "keywords": ...}]
        self._categories_cache: Optional[List[Dict]] = None
        self._categories_cache_ts: float = 0
        # Статистика
        self.stats = {"hits": 0, "misses": 0, "llm_calls": 0, "rule_fallbacks": 0}

    def _get_from_cache(self, key: str) -> Optional[str]:
        """Получить значение из кэша с проверкой TTL"""
        if key in self._description_cache:
            cat_id, ts = self._description_cache[key]
            if time.time() - ts < CACHE_TTL:
                self.stats["hits"] += 1
                return cat_id
            else:
                del self._description_cache[key]
        return None

    def _put_to_cache(self, key: str, category_id: str):
        """Добавить в кэш с TTL, с контролем размера"""
        if len(self._description_cache) >= MAX_CACHE_SIZE:
            # Удаляем самые старые 20% записей
            sorted_items = sorted(self._description_cache.items(), key=lambda x: x[1][1])
            cutoff = int(MAX_CACHE_SIZE * 0.2)
            for k, _ in sorted_items[:cutoff]:
                del self._description_cache[k]
            logger.info(f"RAG cache cleanup: removed {cutoff} oldest entries")

        self._description_cache[key] = (category_id, time.time())

    def _get_categories_cached(self, db: Session, expense_only: bool = True) -> List:
        """Кэшированный запрос категорий из БД"""
        now = time.time()
        if self._categories_cache is None or (now - self._categories_cache_ts) > CACHE_TTL:
            query = db.query(Category)
            if expense_only:
                query = query.filter(Category.type == "expense")
            self._categories_cache = query.all()
            self._categories_cache_ts = now
            logger.debug(f"Categories cache refreshed: {len(self._categories_cache)} categories")
        return self._categories_cache

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
        1. Проверка TTL-кэша
        2. Проверка точного совпадения в истории (Adaptive Learning)
        3. Поиск похожих транзакций (Semantic Search)
        4. Анализ с помощью LLM (RAG)
        5. Fallback на правила
        """
        if not description:
            return None

        description_clean = description.strip().lower()
        self.stats["misses"] += 1

        # 0. ПРОВЕРКА КЭША (TTL)
        cached = self._get_from_cache(description_clean)
        if cached:
            self.stats["misses"] -= 1  # Отменяем, это был hit
            return cached

        # 1. ТОЧНОЕ СОВПАДЕНИЕ (быстрый путь)
        exact_match = self._find_exact_match(db, user_id, description_clean)
        if exact_match:
            self._put_to_cache(description_clean, exact_match)
            return exact_match

        # 2. ПОИСК ПОХОЖИХ ТРАНЗАКЦИЙ
        similar_transactions = self._find_similar_transactions(
            db, user_id, description_clean, limit=5
        )

        # 3. RAG: Используем LLM для категоризации на основе контекста
        self.stats["llm_calls"] += 1
        category_id = await self._categorize_with_llm(
            db, description, amount, similar_transactions
        )

        if category_id:
            self._put_to_cache(description_clean, category_id)
            return category_id

        # 4. FALLBACK: Правила на основе ключевых слов
        self.stats["rule_fallbacks"] += 1
        rule_result = self._rule_based_categorization(db, description_clean)
        if rule_result:
            self._put_to_cache(description_clean, rule_result)
        return rule_result

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
        Дедупликация по описанию для разнообразия контекста.
        """
        keywords = description.split()[:3]

        seen_descriptions = set()
        similar = []

        for keyword in keywords:
            if len(keyword) < 2:
                continue

            results = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                func.lower(Transaction.description).like(f'%{keyword}%'),
                Transaction.category_id.isnot(None)
            ).limit(limit).all()

            for txn in results:
                desc_key = txn.description.lower().strip()
                if txn.category and desc_key not in seen_descriptions:
                    seen_descriptions.add(desc_key)
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
        categories = self._get_categories_cached(db, expense_only=True)
        category_list = [{"name": c.name, "keywords": c.keywords} for c in categories]

        prompt = self._build_rag_prompt(
            description, amount, similar_transactions, category_list
        )

        try:
            response = await ollama_client.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=50
            )

            predicted_category = response.strip().strip('"').strip("'")

            # Ищем в кэшированных категориях сначала
            for cat in categories:
                if cat.name.lower() == predicted_category.lower():
                    logger.info(f"RAG categorized '{description}' as '{cat.name}'")
                    return cat.id

            # Fallback на БД-запрос если кэш устарел
            category = db.query(Category).filter(
                func.lower(Category.name) == predicted_category.lower()
            ).first()

            if category:
                logger.info(f"RAG categorized '{description}' as '{category.name}' (DB lookup)")
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
        categories = self._get_categories_cached(db, expense_only=False)

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

    def get_cache_stats(self) -> Dict:
        """Статистика кэша для мониторинга"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        return {
            "cache_size": len(self._description_cache),
            "max_cache_size": MAX_CACHE_SIZE,
            "cache_ttl_seconds": CACHE_TTL,
            "total_requests": total,
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "hit_rate_percent": round(hit_rate, 1),
            "llm_calls": self.stats["llm_calls"],
            "rule_fallbacks": self.stats["rule_fallbacks"]
        }

    def clear_cache(self):
        """Очистка кэша (например, при изменении категорий)"""
        self._description_cache.clear()
        self._categories_cache = None
        logger.info("RAG classifier cache cleared")


# Глобальный экземпляр RAG классификатора
rag_classifier = RAGClassifier()

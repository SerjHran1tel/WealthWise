from sqlalchemy.orm import Session
from app.models import Category, Transaction


class ClassifierAgent:
    def categorize(self, db: Session, description: str, amount: float) -> str:
        """
        Умная категоризация:
        1. Проверка истории (Adaptive Learning) - ищем точное совпадение описания.
        2. Проверка ключевых слов (Rule-based).
        3. Fallback (None).
        """
        if not description:
            return None

        description_clean = description.strip()

        # 1. ADAPTIVE LEARNING (Учимся на прошлых данных)
        # Ищем последнюю транзакцию с таким же описанием, у которой УЖЕ проставлена категория.
        # Это позволяет системе "запоминать", если пользователь вручную исправил категорию ранее.
        history_match = db.query(Transaction).filter(
            Transaction.description == description_clean,
            Transaction.category_id.isnot(None)
        ).order_by(Transaction.date.desc()).first()

        if history_match:
            # print(f"Adaptive match for '{description}': found {history_match.category.name}")
            return history_match.category_id

        # 2. RULE-BASED (Ключевые слова)
        description_lower = description.lower()
        categories = db.query(Category).all()

        for cat in categories:
            if not cat.keywords:
                continue

            for keyword in cat.keywords:
                # Простая проверка вхождения подстроки
                if keyword.lower() in description_lower:
                    return cat.id

        # 3. Дополнительные жесткие правила (Fallback)
        if "uber" in description_lower or "yandex" in description_lower:
            transport = next((c for c in categories if c.name == "Транспорт"), None)
            if transport: return transport.id

        if "пятерочка" in description_lower or "магнит" in description_lower:
            food = next((c for c in categories if c.name == "Продукты"), None)
            if food: return food.id

        return None


classifier = ClassifierAgent()
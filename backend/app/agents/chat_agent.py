from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Transaction, Category, Budget
from datetime import datetime


class ChatAgent:
    def process_message(self, db: Session, user_id: str, message: str) -> str:
        """
        Обрабатывает сообщение пользователя и возвращает ответ.
        """
        msg = message.lower().strip()

        # 1. Запрос баланса
        if any(word in msg for word in ["баланс", "сколько денег", "остаток", "ситуация"]):
            return self._get_balance(db, user_id)

        # 2. Запрос расходов по категории
        if "потратил" in msg or "расход" in msg:
            # Пытаемся найти название категории в сообщении
            categories = db.query(Category).all()
            for cat in categories:
                if cat.name.lower() in msg:
                    return self._get_category_spending(db, user_id, cat)

            # Если категория не найдена, но спрашивали про траты
            return "Я не понял, о какой категории речь. Попробуйте: 'Сколько я потратил на Продукты?'"

        # 3. Топ трат
        if "больше всего" in msg or "самая большая" in msg or "топ" in msg:
            return self._get_top_expense(db, user_id)

        # 4. Последние операции
        if "последние" in msg or "операции" in msg:
            return self._get_recent_transactions(db, user_id)

        # 5. Приветствие / Помощь
        if any(word in msg for word in ["привет", "помоги", "умеешь", "start", "help"]):
            return (
                "Привет! Я твой финансовый помощник. Ты можешь спросить меня:\n"
                "- Какой у меня баланс?\n"
                "- Сколько я потратил на Продукты?\n"
                "- Где я потратил больше всего?\n"
                "- Покажи последние операции"
            )

        return "Извините, я пока не понимаю этот вопрос. Попробуйте спросить про баланс или расходы по категории."

    # --- Вспомогательные методы ---

    def _get_balance(self, db: Session, user_id: str) -> str:
        income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id, Transaction.is_income == True
        ).scalar() or 0

        expense = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id, Transaction.is_income == False
        ).scalar() or 0

        balance = income - expense
        return f"Ваш текущий баланс: {balance:,.2f} ₽ (Доходы: {income:,.0f}, Расходы: {expense:,.0f})"

    def _get_category_spending(self, db: Session, user_id: str, category: Category) -> str:
        # Берем траты за текущий месяц (упрощенно)
        current_month = datetime.now().replace(day=1)

        spent = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.category_id == category.id,
            Transaction.is_income == False,
            Transaction.date >= current_month
        ).scalar() or 0

        return f"В этом месяце на категорию '{category.name}' вы потратили {spent:,.2f} ₽."

    def _get_top_expense(self, db: Session, user_id: str) -> str:
        top_txn = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False
        ).order_by(Transaction.amount.desc()).first()

        if not top_txn:
            return "У вас пока нет расходов."

        return f"Ваша самая крупная трата: {top_txn.amount:,.2f} ₽ на '{top_txn.description}' ({top_txn.date.date()})."

    def _get_recent_transactions(self, db: Session, user_id: str) -> str:
        txns = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.date.desc()).limit(3).all()

        if not txns:
            return "Операций не найдено."

        lines = ["Последние операции:"]
        for t in txns:
            sign = "+" if t.is_income else "-"
            lines.append(f"{t.date.date()}: {t.description} ({sign}{t.amount:.0f} ₽)")

        return "\n".join(lines)


chat_agent = ChatAgent()
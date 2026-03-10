from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from backend.app.models import Transaction, Budget, Insight


class AnalyticsAgent:
    def run_analysis(self, db: Session, user_id: str):
        """
        Запускает анализ данных и генерирует инсайты.
        """
        # Сначала удаляем старые непрочитанные инсайты, чтобы не спамить
        # (В реальном проекте лучше помечать как archived)
        db.query(Insight).filter(Insight.user_id == user_id, Insight.is_read == False).delete()

        insights = []

        # 1. Поиск крупных трат (Аномалии) > 5000 р
        big_transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.amount > 5000,
            Transaction.is_income == False
        ).order_by(Transaction.date.desc()).limit(3).all()

        for t in big_transactions:
            insights.append(Insight(
                user_id=user_id,
                type="anomaly",
                title=f"Крупная трата: {t.amount:.0f} ₽",
                description=f"Операция '{t.description}' выглядит необычно большой."
            ))

        # 2. Проверка бюджетов (Warnings)
        budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)

        for b in budgets:
            spent = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.category_id == b.category_id,
                Transaction.is_income == False,
                Transaction.date >= current_month_start
            ).scalar() or 0.0

            percentage = (spent / b.amount) * 100

            if percentage > 100:
                insights.append(Insight(
                    user_id=user_id,
                    type="warning",
                    title=f"Превышение бюджета: {b.category.name}",
                    description=f"Вы потратили {spent:.0f} ₽ из {b.amount:.0f} ₽. Лимит превышен на {percentage - 100:.0f}%."
                ))
            elif percentage > 80:
                insights.append(Insight(
                    user_id=user_id,
                    type="warning",
                    title=f"Осторожно: {b.category.name}",
                    description=f"Вы потратили {percentage:.0f}% от бюджета. Осталось мало средств."
                ))

        # 3. Общий совет (Info)
        total_spent = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= current_month_start
        ).scalar() or 0.0

        if total_spent > 0:
            insights.append(Insight(
                user_id=user_id,
                type="info",
                title="Расходы в этом месяце",
                description=f"Всего потрачено {total_spent:.0f} ₽. Продолжайте следить за финансами!"
            ))

        # Сохраняем в БД
        for i in insights:
            db.add(i)
        db.commit()

        return len(insights)


analytics_agent = AnalyticsAgent()
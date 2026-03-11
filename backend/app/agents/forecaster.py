from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from backend.app.models import Transaction, Category, Insight


class ForecastAgent:
    def generate_forecast(self, db: Session, user_id: str):
        """
        Анализирует траты за последние 3 месяца и строит прогноз на следующий.
        Генерирует инсайты типа 'prediction'.
        """
        # 1. Удаляем старые прогнозы, чтобы не дублировать
        db.query(Insight).filter(Insight.user_id == user_id, Insight.type == "prediction").delete()

        now = datetime.now()
        categories = db.query(Category).filter(Category.type == "expense").all()

        insights = []
        total_predicted = 0

        for cat in categories:
            # Считаем среднее за последние 3 месяца
            history_sum = 0
            months_count = 0

            for i in range(1, 4):  # 1, 2, 3 месяца назад
                # Вычисляем дату в прошлом месяце
                prev_date = now - timedelta(days=30 * i)

                monthly_spend = db.query(func.sum(Transaction.amount)).filter(
                    Transaction.user_id == user_id,
                    Transaction.category_id == cat.id,
                    Transaction.is_income == False,
                    extract('month', Transaction.date) == prev_date.month,
                    extract('year', Transaction.date) == prev_date.year
                ).scalar() or 0

                if monthly_spend > 0:
                    history_sum += monthly_spend
                    months_count += 1

            if months_count > 0:
                avg_spend = history_sum / months_count
                total_predicted += avg_spend

                # Если прогнозируемая сумма существенна (> 1000р), создаем инсайт
                if avg_spend > 1000:
                    insights.append(Insight(
                        user_id=user_id,
                        type="prediction",
                        title=f"Прогноз: {cat.name}",
                        description=f"Исходя из прошлых месяцев, ожидаемые траты: ~{avg_spend:,.0f} ₽"
                    ))

        # Общий прогноз на месяц
        if total_predicted > 0:
            insights.insert(0, Insight(
                user_id=user_id,
                type="prediction",
                title="План на следующий месяц",
                description=f"Ожидаемые обязательные расходы: {total_predicted:,.0f} ₽. Учитывайте это в бюджете."
            ))

        # Сохраняем
        for i in insights:
            db.add(i)

        db.commit()


forecast_agent = ForecastAgent()
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from app.models import Transaction, Budget, Goal, Insight, Category
from decimal import Decimal
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class PredictiveAnalyticsAgent:
    """
    Advanced analytics with ML-inspired predictions and anomaly detection.

    Capabilities:
    - Time series forecasting
    - Behavioral anomaly detection
    - Pattern recognition
    - Risk assessment
    - Personalized insights
    """

    def run_comprehensive_analysis(self, db: Session, user_id: str) -> int:
        """
        Run complete financial analysis suite.
        """
        # Clear old insights
        db.query(Insight).filter(
            Insight.user_id == user_id,
            Insight.is_read == False
        ).delete()

        insights = []

        # 1. ANOMALY DETECTION
        insights.extend(self._detect_anomalies(db, user_id))

        # 2. BUDGET WARNINGS
        insights.extend(self._check_budgets(db, user_id))

        # 3. BEHAVIORAL PATTERNS
        insights.extend(self._analyze_behavior(db, user_id))

        # 4. PREDICTIONS
        insights.extend(self._generate_predictions(db, user_id))

        # 5. OPTIMIZATION OPPORTUNITIES
        insights.extend(self._find_optimizations(db, user_id))

        # 6. GOAL TRACKING
        insights.extend(self._track_goals(db, user_id))

        # Save insights
        for insight in insights:
            db.add(insight)

        db.commit()

        logger.info(f"Generated {len(insights)} insights for user {user_id}")
        return len(insights)

    def _detect_anomalies(self, db: Session, user_id: str) -> List[Insight]:
        """
        Detect spending anomalies using statistical methods.
        """
        insights = []

        # Calculate baseline (last 3 months average)
        three_months_ago = datetime.now() - timedelta(days=90)
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)

        categories = db.query(Category).filter(Category.type == "expense").all()

        for cat in categories:
            # Historical average
            hist_avg = db.query(func.avg(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.category_id == cat.id,
                Transaction.is_income == False,
                Transaction.date >= three_months_ago,
                Transaction.date < current_month
            ).scalar() or 0

            # Current month total
            current_total = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.category_id == cat.id,
                Transaction.is_income == False,
                Transaction.date >= current_month
            ).scalar() or 0

            # Anomaly threshold: 2x average
            if hist_avg > 0 and current_total > hist_avg * 2:
                multiplier = current_total / hist_avg
                insights.append(Insight(
                    user_id=user_id,
                    type="anomaly",
                    title=f"⚠️ Аномальные траты: {cat.name}",
                    description=f"Вы потратили {current_total:,.0f}₽, что в {multiplier:.1f}х раз больше обычного ({hist_avg:,.0f}₽). Проверьте крупные покупки."
                ))

        # Large individual transactions
        large_txns = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.amount > 10000,
            Transaction.date >= current_month
        ).order_by(Transaction.amount.desc()).limit(2).all()

        for t in large_txns:
            insights.append(Insight(
                user_id=user_id,
                type="anomaly",
                title=f"💸 Крупная покупка: {t.amount:,.0f}₽",
                description=f"'{t.description}' — это крупная разовая трата. Убедитесь, что она запланирована."
            ))

        return insights

    def _check_budgets(self, db: Session, user_id: str) -> List[Insight]:
        """
        Check budget compliance with early warnings.
        """
        insights = []
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        budgets = db.query(Budget).filter(Budget.user_id == user_id).all()

        for b in budgets:
            spent = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.category_id == b.category_id,
                Transaction.is_income == False,
                Transaction.date >= current_month
            ).scalar() or Decimal('0')

            spent = float(spent)
            limit = float(b.amount)
            percentage = (spent / limit) * 100 if limit > 0 else 0

            if percentage > 100:
                insights.append(Insight(
                    user_id=user_id,
                    type="warning",
                    title=f"🚨 Бюджет превышен: {b.category.name}",
                    description=f"Лимит пробит на {percentage - 100:.0f}%. Потрачено {spent:,.0f}₽ из {limit:,.0f}₽. Рекомендуем остановить траты в этой категории."
                ))
            elif percentage > 90:
                insights.append(Insight(
                    user_id=user_id,
                    type="warning",
                    title=f"⚡ Близко к лимиту: {b.category.name}",
                    description=f"Осталось всего {limit - spent:,.0f}₽ ({100 - percentage:.0f}%) до конца месяца. Планируйте траты осторожно."
                ))
            elif percentage > 75:
                insights.append(Insight(
                    user_id=user_id,
                    type="info",
                    title=f"📊 Средний расход: {b.category.name}",
                    description=f"Использовано {percentage:.0f}% бюджета. Вы на правильном пути к соблюдению лимита."
                ))

        return insights

    def _analyze_behavior(self, db: Session, user_id: str) -> List[Insight]:
        """
        Analyze spending behavioral patterns.
        """
        insights = []

        # Weekend vs weekday spending
        last_30_days = datetime.now() - timedelta(days=30)
        txns = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= last_30_days
        ).all()

        weekend_total = sum(t.amount for t in txns if t.date.weekday() >= 5)
        weekday_total = sum(t.amount for t in txns if t.date.weekday() < 5)

        if weekend_total > weekday_total * 1.5:
            insights.append(Insight(
                user_id=user_id,
                type="recommendation",
                title="📅 Импульсивные траты в выходные",
                description=f"Вы тратите в {weekend_total / max(weekday_total, 1):.1f}х раз больше в выходные ({weekend_total:,.0f}₽ vs {weekday_total:,.0f}₽). Попробуйте планировать покупки на будни."
            ))

        # Evening spending
        evening_total = sum(t.amount for t in txns if t.date.hour >= 18)
        total = sum(t.amount for t in txns)

        if total > 0 and (evening_total / total) > 0.4:
            insights.append(Insight(
                user_id=user_id,
                type="recommendation",
                title="🌙 Вечерние импульсивные покупки",
                description=f"40%+ трат происходят вечером — это признак эмоциональных покупок. Попробуйте правило '24 часа' перед крупной тратой."
            ))

        # Subscription detection
        recurring = self._detect_recurring_payments(db, user_id)
        if recurring:
            total_recurring = sum(r['amount'] for r in recurring)
            insights.append(Insight(
                user_id=user_id,
                type="info",
                title=f"💳 Регулярные подписки: {total_recurring:,.0f}₽/мес",
                description=f"Найдено {len(recurring)} подписок. Проверьте, все ли они нужны: {', '.join([r['description'] for r in recurring[:3]])}."
            ))

        return insights

    def _generate_predictions(self, db: Session, user_id: str) -> List[Insight]:
        """
        Generate spending predictions using time series analysis.
        """
        insights = []
        categories = db.query(Category).filter(Category.type == "expense").all()

        total_predicted = 0

        for cat in categories:
            # Simple moving average of last 3 months
            prediction = self._predict_category_spending(db, user_id, cat.id)

            if prediction > 1000:
                total_predicted += prediction

                insights.append(Insight(
                    user_id=user_id,
                    type="prediction",
                    title=f"🔮 Прогноз: {cat.name}",
                    description=f"Ожидаемые траты на следующий месяц: ~{prediction:,.0f}₽ (на основе ваших паттернов за 3 месяца)"
                ))

        if total_predicted > 0:
            # Days until month end
            today = datetime.now()
            next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
            days_left = (next_month - today).days

            insights.insert(0, Insight(
                user_id=user_id,
                type="prediction",
                title=f"📈 Прогноз на {next_month.strftime('%B')}",
                description=f"Ожидаемые обязательные расходы: {total_predicted:,.0f}₽. Заложите еще 20% на непредвиденное. До конца месяца {days_left} дней."
            ))

        return insights

    def _predict_category_spending(self, db: Session, user_id: str, category_id: str) -> float:
        """
        Predict next month spending for a category using weighted moving average.
        """
        now = datetime.now()
        predictions = []

        # Get last 3 months
        for i in range(1, 4):
            month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0)

            monthly_spend = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.category_id == category_id,
                Transaction.is_income == False,
                Transaction.date >= month_start,
                Transaction.date < month_end
            ).scalar() or 0

            # Weighted: recent months matter more
            weight = 4 - i  # 3, 2, 1
            predictions.append(float(monthly_spend) * weight)

        if not predictions:
            return 0

        # Weighted average
        return sum(predictions) / sum([3, 2, 1])

    def _find_optimizations(self, db: Session, user_id: str) -> List[Insight]:
        """
        Find opportunities to optimize spending.
        """
        insights = []
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)

        # Find expensive categories
        expensive_cats = db.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= current_month
        ).group_by(Category.name).order_by(func.sum(Transaction.amount).desc()).limit(3).all()

        for cat_name, total in expensive_cats:
            if total > 5000:  # Significant amount
                # Calculate potential savings (realistic 10-15%)
                savings = total * 0.12
                insights.append(Insight(
                    user_id=user_id,
                    type="recommendation",
                    title=f"💡 Оптимизация: {cat_name}",
                    description=f"Это ваша топ-категория трат ({total:,.0f}₽). Экономия 10-15% = {savings:,.0f}₽/мес = {savings * 12:,.0f}₽/год!"
                ))

        return insights

    def _track_goals(self, db: Session, user_id: str) -> List[Insight]:
        """
        Track goal progress and provide motivation.
        """
        insights = []
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()

        balance_info = self._get_balance_info(db, user_id)
        monthly_surplus = balance_info['balance']

        for goal in goals:
            remaining = float(goal.target_amount) - float(goal.current_amount)
            percentage = (float(goal.current_amount) / float(goal.target_amount) * 100) if goal.target_amount > 0 else 0

            if percentage >= 100:
                insights.append(Insight(
                    user_id=user_id,
                    type="info",
                    title=f"🎉 Цель достигнута: {goal.name}!",
                    description=f"Поздравляем! Вы накопили {goal.target_amount:,.0f}₽. Время реализовать мечту!"
                ))
            elif percentage >= 75:
                insights.append(Insight(
                    user_id=user_id,
                    type="info",
                    title=f"🎯 Почти у цели: {goal.name}",
                    description=f"Осталось {remaining:,.0f}₽ ({100 - percentage:.0f}%). Вы на финишной прямой!"
                ))
            else:
                # Calculate months needed
                if monthly_surplus > 0:
                    months_needed = remaining / monthly_surplus
                    insights.append(Insight(
                        user_id=user_id,
                        type="info",
                        title=f"📊 Прогресс: {goal.name}",
                        description=f"При текущем темпе сбережений цель будет достигнута через {months_needed:.1f} мес. Осталось {remaining:,.0f}₽."
                    ))

        return insights

    def _detect_recurring_payments(self, db: Session, user_id: str) -> List[Dict]:
        """
        Detect recurring payments (subscriptions).
        """
        # Look for similar amounts and descriptions
        last_90_days = datetime.now() - timedelta(days=90)

        txns = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= last_90_days
        ).all()

        # Group by similar descriptions and amounts
        recurring = {}
        for t in txns:
            key = (t.description.lower()[:20], round(t.amount, -2))  # Rounded amount
            if key not in recurring:
                recurring[key] = []
            recurring[key].append(t.date)

        # Filter: appeared 2+ times
        subscriptions = []
        for (desc, amount), dates in recurring.items():
            if len(dates) >= 2:
                subscriptions.append({
                    'description': desc,
                    'amount': amount,
                    'frequency': len(dates)
                })

        return subscriptions

    def _get_balance_info(self, db: Session, user_id: str) -> Dict:
        """Get current financial balance."""
        income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == True
        ).scalar() or Decimal('0')

        expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False
        ).scalar() or Decimal('0')

        income = Decimal(str(income)) if income else Decimal('0')
        expenses = Decimal(str(expenses)) if expenses else Decimal('0')

        return {
            'income': float(income),
            'expenses': float(expenses),
            'balance': float(income - expenses)
        }


# Global instance
predictive_analytics_agent = PredictiveAnalyticsAgent()
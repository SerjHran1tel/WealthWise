from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models import Transaction, Budget, Goal, Insight, Category
from app.services.ollama_client import ollama_client
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class ReportAgent:
    """
    Агент для генерации еженедельных отчётов и персонализированных рекомендаций.
    """

    async def generate_weekly_report(self, db: Session, user_id: str) -> Dict:
        """
        Генерирует еженедельный отчёт с аналитикой и рекомендациями.
        """
        # Собираем данные за последние 7 дней
        week_ago = datetime.now() - timedelta(days=7)

        # Статистика
        stats = self._get_weekly_stats(db, user_id, week_ago)

        # Сравнение с предыдущей неделей
        comparison = self._compare_with_previous_week(db, user_id, week_ago)

        # Топ категорий расходов
        top_categories = self._get_top_categories(db, user_id, week_ago)

        # Проблемные области
        issues = self._detect_issues(db, user_id, stats, top_categories)

        # Генерируем персонализированные рекомендации с помощью LLM
        recommendations = await self._generate_recommendations(
            stats, comparison, top_categories, issues
        )

        # Прогресс по целям
        goals_progress = self._get_goals_progress(db, user_id)

        # Сохраняем отчёт как инсайт
        self._save_report_insight(db, user_id, stats, recommendations)

        return {
            "period": f"{week_ago.strftime('%d.%m')} - {datetime.now().strftime('%d.%m')}",
            "stats": stats,
            "comparison": comparison,
            "top_categories": top_categories,
            "issues": issues,
            "recommendations": recommendations,
            "goals_progress": goals_progress
        }

    def _get_weekly_stats(
            self,
            db: Session,
            user_id: str,
            since: datetime
    ) -> Dict:
        """Статистика за неделю"""

        income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == True,
            Transaction.date >= since
        ).scalar() or 0.0

        expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= since
        ).scalar() or 0.0

        transactions_count = db.query(func.count(Transaction.id)).filter(
            Transaction.user_id == user_id,
            Transaction.date >= since
        ).scalar() or 0

        avg_transaction = expenses / transactions_count if transactions_count > 0 else 0

        return {
            "income": float(income),
            "expenses": float(expenses),
            "balance": float(income - expenses),
            "transactions_count": transactions_count,
            "avg_transaction": float(avg_transaction)
        }

    def _compare_with_previous_week(
            self,
            db: Session,
            user_id: str,
            current_week_start: datetime
    ) -> Dict:
        """Сравнение с предыдущей неделей"""

        prev_week_start = current_week_start - timedelta(days=7)

        prev_expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= prev_week_start,
            Transaction.date < current_week_start
        ).scalar() or 0.0

        current_expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= current_week_start
        ).scalar() or 0.0

        if prev_expenses > 0:
            change_percent = ((current_expenses - prev_expenses) / prev_expenses) * 100
        else:
            change_percent = 0

        return {
            "prev_week_expenses": float(prev_expenses),
            "current_week_expenses": float(current_expenses),
            "change_percent": round(change_percent, 1),
            "trend": "up" if change_percent > 0 else "down" if change_percent < 0 else "stable"
        }

    def _get_top_categories(
            self,
            db: Session,
            user_id: str,
            since: datetime,
            limit: int = 5
    ) -> List[Dict]:
        """Топ категорий по расходам за неделю"""

        results = db.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= since
        ).group_by(Category.name).order_by(func.sum(Transaction.amount).desc()).limit(limit).all()

        return [
            {"category": r.name, "amount": float(r.total)}
            for r in results
        ]

    def _detect_issues(
            self,
            db: Session,
            user_id: str,
            stats: Dict,
            top_categories: List[Dict]
    ) -> List[str]:
        """Выявление проблемных областей"""

        issues = []

        # Проверка превышения бюджетов
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        budgets = db.query(Budget).filter(Budget.user_id == user_id).all()

        for budget in budgets:
            spent = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.category_id == budget.category_id,
                Transaction.is_income == False,
                Transaction.date >= current_month
            ).scalar() or 0.0

            if spent > budget.amount:
                issues.append(
                    f"Превышен бюджет на '{budget.category.name}': "
                    f"{spent:.0f} ₽ из {budget.amount:.0f} ₽"
                )

        # Проверка необычно высоких расходов
        if stats['avg_transaction'] > 5000:
            issues.append(f"Средний чек очень высокий: {stats['avg_transaction']:.0f} ₽")

        # Проверка негативного баланса
        if stats['balance'] < 0:
            issues.append(f"Отрицательный баланс за неделю: {stats['balance']:.0f} ₽")

        return issues

    async def _generate_recommendations(
            self,
            stats: Dict,
            comparison: Dict,
            top_categories: List[Dict],
            issues: List[str]
    ) -> List[str]:
        """Генерация персонализированных рекомендаций с помощью LLM"""

        prompt = self._build_recommendations_prompt(stats, comparison, top_categories, issues)

        try:
            response = await ollama_client.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=500
            )

            # Парсим рекомендации (каждая с новой строки)
            recommendations = [
                line.strip().lstrip('•-–—').strip()
                for line in response.split('\n')
                if line.strip() and len(line.strip()) > 10
            ]

            return recommendations[:5]  # Топ-5 рекомендаций

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            return [
                "Отслеживайте ежедневные расходы",
                "Установите бюджеты для крупных категорий",
                "Анализируйте чеки перед покупками"
            ]

    def _build_recommendations_prompt(
            self,
            stats: Dict,
            comparison: Dict,
            top_categories: List[Dict],
            issues: List[str]
    ) -> str:
        """Формирует промпт для генерации рекомендаций"""

        prompt_parts = [
            "Ты - финансовый консультант. Проанализируй данные пользователя и дай 3-5 конкретных рекомендаций.",
            "",
            "ДАННЫЕ ЗА НЕДЕЛЮ:",
            f"- Доходы: {stats['income']:.0f} ₽",
            f"- Расходы: {stats['expenses']:.0f} ₽",
            f"- Баланс: {stats['balance']:.0f} ₽",
            f"- Средний чек: {stats['avg_transaction']:.0f} ₽",
            "",
            "СРАВНЕНИЕ С ПРОШЛОЙ НЕДЕЛЕЙ:",
            f"- Изменение расходов: {comparison['change_percent']:+.1f}%",
            f"- Тренд: {comparison['trend']}",
            "",
            "ТОП КАТЕГОРИЙ РАСХОДОВ:"
        ]

        for cat in top_categories[:3]:
            prompt_parts.append(f"- {cat['category']}: {cat['amount']:.0f} ₽")

        if issues:
            prompt_parts.append("")
            prompt_parts.append("ПРОБЛЕМЫ:")
            for issue in issues:
                prompt_parts.append(f"- {issue}")

        prompt_parts.extend([
            "",
            "ЗАДАЧА: Дай 3-5 конкретных, практичных рекомендаций на русском языке.",
            "Формат: каждая рекомендация с новой строки, без нумерации.",
            "Фокус на действиях, которые пользователь может предпринять.",
            "",
            "РЕКОМЕНДАЦИИ:"
        ])

        return "\n".join(prompt_parts)

    def _get_goals_progress(self, db: Session, user_id: str) -> List[Dict]:
        """Прогресс по финансовым целям"""

        goals = db.query(Goal).filter(Goal.user_id == user_id).all()

        return [
            {
                "name": g.name,
                "current": float(g.current_amount),
                "target": float(g.target_amount),
                "percentage": round((g.current_amount / g.target_amount * 100), 1) if g.target_amount > 0 else 0
            }
            for g in goals
        ]

    def _save_report_insight(
            self,
            db: Session,
            user_id: str,
            stats: Dict,
            recommendations: List[str]
    ):
        """Сохраняет отчёт как инсайт"""

        # Удаляем старые еженедельные отчёты
        db.query(Insight).filter(
            Insight.user_id == user_id,
            Insight.type == "weekly_report"
        ).delete()

        # Создаём новый отчёт
        report_text = f"Расходы: {stats['expenses']:.0f} ₽. "
        if recommendations:
            report_text += f"Совет: {recommendations[0]}"

        insight = Insight(
            user_id=user_id,
            type="weekly_report",
            title="📊 Еженедельный отчёт",
            description=report_text
        )

        db.add(insight)
        db.commit()


# Глобальный экземпляр агента отчётов
report_agent = ReportAgent()
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from backend.app.models import Transaction, Budget, Goal, Insight, Category
from backend.app.services.ollama_client import ollama_client
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class WeeklyReportAgent:
    """
    Автоматический агент для генерации еженедельных отчетов.

    Возможности:
    - Автоматическая генерация отчетов каждый понедельник в 9:00
    - Анализ трат за прошедшую неделю
    - Сравнение с предыдущими неделями
    - AI-generated персонализированные рекомендации
    - Предложение конкретных действий
    """

    async def generate_weekly_report(self, db: Session, user_id: str) -> Dict:
        """
        Генерирует еженедельный отчёт с аналитикой и действиями.
        """
        logger.info(f"Generating weekly report for user {user_id}")

        # Период: последние 7 дней
        week_ago = datetime.now() - timedelta(days=7)
        two_weeks_ago = datetime.now() - timedelta(days=14)

        # Собираем статистику
        stats = self._get_weekly_stats(db, user_id, week_ago)
        comparison = self._compare_with_previous_week(db, user_id, week_ago, two_weeks_ago)
        top_categories = self._get_top_categories(db, user_id, week_ago)
        issues = self._detect_issues(db, user_id, stats, top_categories)

        # AI-generated рекомендации
        recommendations = await self._generate_ai_recommendations(
            db, user_id, stats, comparison, top_categories, issues
        )

        # Конкретные действия
        actions = self._generate_actionable_items(
            db, user_id, stats, top_categories, issues
        )

        # Прогресс по целям
        goals_progress = self._get_goals_progress(db, user_id)

        # Сохраняем отчёт как инсайт
        self._save_report_as_insight(db, user_id, stats, recommendations, actions)

        report = {
            "period": f"{week_ago.strftime('%d.%m')} - {datetime.now().strftime('%d.%m')}",
            "stats": stats,
            "comparison": comparison,
            "top_categories": top_categories,
            "issues": issues,
            "recommendations": recommendations,
            "actions": actions,
            "goals_progress": goals_progress,
            "generated_at": datetime.now().isoformat()
        }

        logger.info(f"Weekly report generated for user {user_id}: {len(actions)} actions proposed")
        return report

    def _get_weekly_stats(self, db: Session, user_id: str, since: datetime) -> Dict:
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
            "avg_transaction": float(avg_transaction),
            "daily_avg": float(expenses / 7) if expenses > 0 else 0
        }

    def _compare_with_previous_week(
            self, db: Session, user_id: str,
            current_week_start: datetime,
            prev_week_start: datetime
    ) -> Dict:
        """Сравнение с предыдущей неделей"""

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
            "change_amount": float(current_expenses - prev_expenses),
            "trend": "up" if change_percent > 5 else "down" if change_percent < -5 else "stable"
        }

    def _get_top_categories(
            self, db: Session, user_id: str, since: datetime, limit: int = 5
    ) -> List[Dict]:
        """Топ категорий по расходам за неделю"""

        results = db.query(
            Category.name,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).join(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= since
        ).group_by(Category.name).order_by(func.sum(Transaction.amount).desc()).limit(limit).all()

        return [
            {
                "category": r.name,
                "amount": float(r.total),
                "transactions_count": r.count,
                "percentage": 0  # Будет рассчитано позже
            }
            for r in results
        ]

    def _detect_issues(
            self, db: Session, user_id: str, stats: Dict, top_categories: List[Dict]
    ) -> List[Dict]:
        """Выявление проблемных областей"""

        issues = []

        # 1. Проверка превышения бюджетов
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
                issues.append({
                    "type": "budget_exceeded",
                    "severity": "high",
                    "category": budget.category.name if budget.category else "Unknown",
                    "message": f"Превышен бюджет на '{budget.category.name}': {spent:.0f}₽ из {budget.amount:.0f}₽",
                    "overspend": float(spent - budget.amount)
                })
            elif spent > budget.amount * 0.9:
                issues.append({
                    "type": "budget_warning",
                    "severity": "medium",
                    "category": budget.category.name if budget.category else "Unknown",
                    "message": f"Близко к лимиту '{budget.category.name}': {spent:.0f}₽ из {budget.amount:.0f}₽",
                    "remaining": float(budget.amount - spent)
                })

        # 2. Высокий средний чек
        if stats['avg_transaction'] > 3000:
            issues.append({
                "type": "high_avg_transaction",
                "severity": "medium",
                "message": f"Средний чек очень высокий: {stats['avg_transaction']:.0f}₽",
                "suggestion": "Возможно, много крупных покупок"
            })

        # 3. Негативный баланс за неделю
        if stats['balance'] < 0:
            issues.append({
                "type": "negative_balance",
                "severity": "high",
                "message": f"Отрицательный баланс за неделю: {stats['balance']:.0f}₽",
                "suggestion": "Расходы превысили доходы"
            })

        # 4. Рост трат на 20%+
        return issues

    async def _generate_ai_recommendations(
            self,
            db: Session,
            user_id: str,
            stats: Dict,
            comparison: Dict,
            top_categories: List[Dict],
            issues: List[Dict]
    ) -> List[str]:
        """Генерация персонализированных рекомендаций с помощью AI"""

        prompt = self._build_recommendations_prompt(
            stats, comparison, top_categories, issues
        )

        try:
            # Получаем персонализированный system prompt
            from backend.app.agents.user_profiler import user_profiler
            system_prompt = user_profiler.get_personalized_system_prompt(db, user_id)

            response = await ollama_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=600
            )

            # Парсим рекомендации
            recommendations = [
                line.strip().lstrip('•-–—1234567890.').strip()
                for line in response.split('\n')
                if line.strip() and len(line.strip()) > 20
            ]

            return recommendations[:5]

        except Exception as e:
            logger.error(f"Error generating AI recommendations: {e}", exc_info=True)
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
            issues: List[Dict]
    ) -> str:
        """Формирует промпт для генерации рекомендаций"""

        prompt_parts = [
            "📊 ЕЖЕНЕДЕЛЬНЫЙ ФИНАНСОВЫЙ ОТЧЁТ",
            "",
            "СТАТИСТИКА ЗА НЕДЕЛЮ:",
            f"• Расходы: {stats['expenses']:.0f}₽ (средний чек: {stats['avg_transaction']:.0f}₽)",
            f"• Доходы: {stats['income']:.0f}₽",
            f"• Баланс: {stats['balance']:.0f}₽",
            f"• Количество операций: {stats['transactions_count']}",
            "",
            "СРАВНЕНИЕ С ПРОШЛОЙ НЕДЕЛЕЙ:",
            f"• Изменение расходов: {comparison['change_percent']:+.1f}% ({comparison['trend']})",
            f"• Разница: {comparison['change_amount']:+.0f}₽",
            "",
            "ТОП-3 КАТЕГОРИИ РАСХОДОВ:"
        ]

        for i, cat in enumerate(top_categories[:3], 1):
            prompt_parts.append(f"{i}. {cat['category']}: {cat['amount']:.0f}₽ ({cat['transactions_count']} операций)")

        if issues:
            prompt_parts.append("")
            prompt_parts.append("⚠️ ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ:")
            for issue in issues[:3]:
                prompt_parts.append(f"• {issue['message']}")

        prompt_parts.extend([
            "",
            "🎯 ТВОЯ ЗАДАЧА:",
            "Дай 3-5 КОНКРЕТНЫХ, ПЕРСОНАЛИЗИРОВАННЫХ рекомендаций:",
            "1. Учитывай финансовый профиль пользователя",
            "2. Фокусируйся на ДЕЙСТВИЯХ, а не на проблемах",
            "3. Каждая рекомендация = конкретный шаг",
            "4. Будь эмпатичным, но честным",
            "5. Предлагай измеримые улучшения",
            "",
            "Формат: каждая рекомендация с новой строки, БЕЗ нумерации.",
            "",
            "РЕКОМЕНДАЦИИ:"
        ])

        return "\n".join(prompt_parts)

    def _generate_actionable_items(
            self,
            db: Session,
            user_id: str,
            stats: Dict,
            top_categories: List[Dict],
            issues: List[Dict]
    ) -> List[Dict]:
        """
        Генерирует конкретные действия которые пользователь может предпринять.
        """
        actions = []

        # 1. ДЕЙСТВИЯ ПО БЮДЖЕТАМ
        for issue in issues:
            if issue['type'] == 'budget_exceeded':
                actions.append({
                    "id": f"budget_{issue['category']}",
                    "type": "budget_adjustment",
                    "priority": "high",
                    "title": f"Пересмотреть бюджет: {issue['category']}",
                    "description": f"Вы превысили лимит на {issue['overspend']:.0f}₽. Либо увеличьте бюджет, либо сократите траты.",
                    "actions": [
                        {"label": "Увеличить бюджет", "action": "increase_budget"},
                        {"label": "Проанализировать траты", "action": "analyze_category"},
                        {"label": "Установить предупреждение", "action": "set_alert"}
                    ]
                })

        # 2. ОПТИМИЗАЦИЯ ТОП КАТЕГОРИЙ
        if top_categories:
            top_cat = top_categories[0]
            if top_cat['amount'] > 10000:
                actions.append({
                    "id": f"optimize_{top_cat['category']}",
                    "type": "optimization",
                    "priority": "medium",
                    "title": f"Оптимизировать: {top_cat['category']}",
                    "description": f"Это ваша топ-категория ({top_cat['amount']:.0f}₽). Экономия 10% = {top_cat['amount'] * 0.1:.0f}₽/неделю.",
                    "actions": [
                        {"label": "Посмотреть все траты", "action": "view_transactions"},
                        {"label": "Установить бюджет", "action": "create_budget"},
                        {"label": "Найти альтернативы", "action": "find_alternatives"}
                    ]
                })

        # 3. ДЕЙСТВИЯ ПО ЦЕЛЯМ
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()

        for goal in goals:
            percentage = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0

            if percentage < 50 and goal.current_amount > 0:
                # Цель далека от завершения
                remaining = goal.target_amount - goal.current_amount
                weekly_need = remaining / 12  # Предполагаем достижение за 3 месяца

                if stats['balance'] > 0:
                    actions.append({
                        "id": f"goal_{goal.id}",
                        "type": "goal_progress",
                        "priority": "medium",
                        "title": f"Ускорить цель: {goal.name}",
                        "description": f"Откладывайте {weekly_need:.0f}₽/неделю чтобы достичь цели за 3 месяца.",
                        "actions": [
                            {"label": "Пополнить сейчас", "action": "deposit_to_goal"},
                            {"label": "Настроить автоплатеж", "action": "setup_autopay"},
                            {"label": "Пересмотреть цель", "action": "adjust_goal"}
                        ]
                    })

        # 4. ДЕЙСТВИЯ ПО ПОДПИСКАМ (если обнаружены)
        subscriptions = self._detect_subscriptions(db, user_id)
        if subscriptions:
            total_subs = sum(s['amount'] for s in subscriptions)
            actions.append({
                "id": "subscriptions_review",
                "type": "subscription_audit",
                "priority": "high",
                "title": f"Проверить подписки: {total_subs:.0f}₽/мес",
                "description": f"Найдено {len(subscriptions)} регулярных платежей. Все ли они нужны?",
                "subscriptions": subscriptions,
                "actions": [
                    {"label": "Отменить неиспользуемые", "action": "cancel_subscriptions"},
                    {"label": "Пометить как важные", "action": "mark_essential"},
                    {"label": "Напомнить через месяц", "action": "snooze"}
                ]
            })

        # 5. ЕЖЕДНЕВНЫЙ ЛИМИТ (если траты высокие)
        if stats['daily_avg'] > 2000:
            actions.append({
                "id": "daily_limit",
                "type": "spending_control",
                "priority": "medium",
                "title": "Установить дневной лимит",
                "description": f"Вы тратите в среднем {stats['daily_avg']:.0f}₽/день. Установите дневной лимит для контроля.",
                "actions": [
                    {"label": "Лимит 1,500₽/день", "action": "set_limit_1500"},
                    {"label": "Лимит 2,000₽/день", "action": "set_limit_2000"},
                    {"label": "Настроить свой лимит", "action": "custom_limit"}
                ]
            })

        # Сортируем по приоритету
        priority_order = {"high": 0, "medium": 1, "low": 2}
        actions.sort(key=lambda x: priority_order.get(x['priority'], 3))

        return actions[:5]  # Максимум 5 действий

    def _detect_subscriptions(self, db: Session, user_id: str) -> List[Dict]:
        """Определяет регулярные подписки"""

        last_60_days = datetime.now() - timedelta(days=60)

        txns = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= last_60_days
        ).all()

        # Группируем по схожим описаниям и суммам
        recurring = {}
        for t in txns:
            key = (t.description.lower()[:20], round(float(t.amount), -2))
            if key not in recurring:
                recurring[key] = []
            recurring[key].append(t.date)

        # Фильтруем: встречается 2+ раза
        subscriptions = []
        for (desc, amount), dates in recurring.items():
            if len(dates) >= 2:
                subscriptions.append({
                    'description': desc,
                    'amount': amount,
                    'frequency': len(dates)
                })

        return subscriptions

    def _get_goals_progress(self, db: Session, user_id: str) -> List[Dict]:
        """Прогресс по финансовым целям"""

        goals = db.query(Goal).filter(Goal.user_id == user_id).all()

        return [
            {
                "name": g.name,
                "current": float(g.current_amount),
                "target": float(g.target_amount),
                "percentage": round((g.current_amount / g.target_amount * 100), 1) if g.target_amount > 0 else 0,
                "status": "completed" if g.current_amount >= g.target_amount else "in_progress"
            }
            for g in goals
        ]

    def _save_report_as_insight(
            self,
            db: Session,
            user_id: str,
            stats: Dict,
            recommendations: List[str],
            actions: List[Dict]
    ):
        """Сохраняет отчёт как инсайт для отображения в UI"""

        # Удаляем старые еженедельные отчёты
        db.query(Insight).filter(
            Insight.user_id == user_id,
            Insight.type == "weekly_report"
        ).delete()

        # Формируем краткое описание
        report_summary = f"Расходы: {stats['expenses']:.0f}₽. "

        if recommendations:
            report_summary += f"Совет: {recommendations[0][:100]}"

        if actions:
            report_summary += f" | {len(actions)} действий к выполнению"

        # Создаём инсайт
        insight = Insight(
            user_id=user_id,
            type="weekly_report",
            title="📊 Еженедельный отчёт",
            description=report_summary
        )

        db.add(insight)
        db.commit()

        logger.info(f"Saved weekly report as insight for user {user_id}")


# Global instance
weekly_report_agent = WeeklyReportAgent()
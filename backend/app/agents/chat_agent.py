import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
import logging

from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta

from backend.app.models import Transaction, Category, Budget, Goal, Insight
from backend.app.services.ollama_client import ollama_client, OllamaError

logger = logging.getLogger(__name__)


class ChatAgent:
    """
    AI ассистент на базе Ollama с доступом к финансовой БД.
    """

    def __init__(self):
        self.system_prompt = """Ты - продвинутый финансовый помощник WealthWise с глубоким пониманием личных финансов.

ТВОИ ВОЗМОЖНОСТИ:
- Анализ финансовых паттернов и трендов
- Выявление аномалий и рисков
- Персонализированные рекомендации по экономии
- Прогнозирование будущих расходов
- Помощь в достижении финансовых целей

ПРАВИЛА ОБЩЕНИЯ:
1. Отвечай КРАТКО и КОНКРЕТНО (2-4 предложения)
2. Используй ФАКТЫ из предоставленных данных, когда речь о финансах
3. Форматируй суммы с пробелами и знаком ₽ (например: 15 000 ₽)
4. Будь дружелюбным, но профессиональным
5. При отсутствии данных - честно признавай это

ЧТО ЗАПРЕЩЕНО:
- Длинные объяснения (>4 предложений)
- Придумывание данных
- Общие советы без контекста
- Markdown форматирование (**, ##, -)
- Финансовые советы в стиле "купи акции"

СТИЛЬ:
- Как опытный финансовый консультант
- С эмпатией к финансовым целям пользователя
- С акцентом на действия, а не теорию

Всегда отвечай на русском языке."""

    async def process_message(self, db: Session, user_id: str, message: str) -> str:
        """
        Обрабатывает сообщение пользователя с помощью Ollama.
        """
        try:
            context = self._gather_context(db, user_id, message)
            prompt = self._build_prompt(message, context)

            response = await ollama_client.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.3,
                max_tokens=1000  # значение можно изменить в настройках
            )

            # Возвращаем ответ без искусственной обрезки
            return response.strip()

        except OllamaError as e:
            logger.error(f"Ollama error: {e}")
            return "Извините, AI ассистент временно недоступен. Попробуйте позже или проверьте, что Ollama запущен."
        except Exception as e:
            logger.error(f"Chat agent error: {e}", exc_info=True)
            return "Произошла ошибка при обработке запроса. Попробуйте переформулировать вопрос."

    def _format_amount(self, value: float) -> str:
        """Форматирует сумму с пробелами и знаком рубля (целые числа)."""
        return f"{int(round(value)):,}".replace(',', ' ') + ' ₽'

    def _parse_period(self, message: str) -> Optional[Dict[str, datetime]]:
        """
        Пытается извлечь из сообщения период для отчёта.
        Возвращает словарь с start_date и end_date (datetime) или None.
        """
        msg_lower = message.lower()
        today = datetime.now().date()

        # Последний месяц
        if re.search(r'последн\w+\s+месяц|прошл\w+\s+месяц|за\s+месяц', msg_lower):
            start_date = today.replace(day=1) - relativedelta(months=1)
            end_date = today.replace(day=1) - timedelta(days=1)
            return {
                'start_date': datetime.combine(start_date, datetime.min.time()),
                'end_date': datetime.combine(end_date, datetime.max.time())
            }

        # Текущий месяц
        if re.search(r'текущ\w+\s+месяц|этот\s+месяц', msg_lower):
            start_date = today.replace(day=1)
            end_date = today
            return {
                'start_date': datetime.combine(start_date, datetime.min.time()),
                'end_date': datetime.combine(end_date, datetime.max.time())
            }

        # Последние 7 дней / неделя
        if re.search(r'последн\w+\s+7\s+дней|последн\w+\s+недел\w+|за\s+недел\w+', msg_lower):
            start_date = today - timedelta(days=7)
            end_date = today
            return {
                'start_date': datetime.combine(start_date, datetime.min.time()),
                'end_date': datetime.combine(end_date, datetime.max.time())
            }

        # Конкретный месяц: февраль 2026
        months_map = {
            'январ': 1, 'феврал': 2, 'март': 3, 'апрел': 4, 'май': 5, 'июн': 6,
            'июл': 7, 'август': 8, 'сентябр': 9, 'октябр': 10, 'ноябр': 11, 'декабр': 12
        }
        for month_name, month_num in months_map.items():
            if month_name in msg_lower:
                year_match = re.search(r'\b(20\d{2})\b', msg_lower)
                if year_match:
                    year = int(year_match.group(1))
                else:
                    year = today.year
                    if month_num > today.month:
                        year -= 1
                start_date = datetime(year, month_num, 1)
                if month_num == 12:
                    end_date = datetime(year, 12, 31)
                else:
                    end_date = datetime(year, month_num + 1, 1) - timedelta(days=1)
                return {
                    'start_date': start_date,
                    'end_date': datetime.combine(end_date.date(), datetime.max.time())
                }

        return None

    def _get_balance_for_period(self, db: Session, user_id: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Возвращает статистику за указанный период.
        """
        income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == True,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or Decimal('0')

        expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or Decimal('0')

        income = float(Decimal(str(income))) if income else 0.0
        expenses = float(Decimal(str(expenses))) if expenses else 0.0

        # Топ категорий расходов за период
        expenses_by_cat = db.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Category.name).order_by(desc('total')).limit(3).all()

        top_categories = [{'category': cat.name, 'amount': float(cat.total)} for cat in expenses_by_cat]

        # Сравнение с предыдущим аналогичным периодом
        delta = end_date - start_date
        prev_start = start_date - delta
        prev_end = start_date - timedelta(seconds=1)

        prev_income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == True,
            Transaction.date >= prev_start,
            Transaction.date <= prev_end
        ).scalar() or Decimal('0')

        prev_expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= prev_start,
            Transaction.date <= prev_end
        ).scalar() or Decimal('0')

        prev_income = float(Decimal(str(prev_income))) if prev_income else 0.0
        prev_expenses = float(Decimal(str(prev_expenses))) if prev_expenses else 0.0

        return {
            'period_start': start_date.strftime('%d.%m.%Y'),
            'period_end': end_date.strftime('%d.%m.%Y'),
            'income': income,
            'expenses': expenses,
            'balance': income - expenses,
            'top_expense_categories': top_categories,
            'prev_income': prev_income,
            'prev_expenses': prev_expenses,
            'prev_balance': prev_income - prev_expenses
        }

    def _gather_context(self, db: Session, user_id: str, message: str) -> Dict:
        """
        Собирает релевантный контекст из БД на основе сообщения пользователя.
        """
        msg_lower = message.lower()
        context = {}

        # Проверяем, запрашивает ли пользователь отчёт за период
        period = self._parse_period(message)
        if period:
            context['period_balance'] = self._get_balance_for_period(db, user_id, period['start_date'], period['end_date'])
            context['period_expenses_by_category'] = self._get_expenses_by_category(
                db, user_id, start_date=period['start_date'], end_date=period['end_date']
            )
            context['period_top_expenses'] = self._get_top_expenses(
                db, user_id, limit=3, start_date=period['start_date'], end_date=period['end_date']
            )
        else:
            # Всегда добавляем базовую статистику
            context['balance'] = self._get_balance_info(db, user_id)

            # Если спрашивают про баланс или общую ситуацию
            if any(word in msg_lower for word in ['баланс', 'сколько', 'деньги', 'ситуация', 'статус']):
                context['recent_transactions'] = self._get_recent_transactions(db, user_id, limit=5)

            # Если спрашивают про расходы/категории
            if any(word in msg_lower for word in ['потратил', 'расход', 'трат', 'категор']):
                context['expenses_by_category'] = self._get_expenses_by_category(db, user_id)
                context['top_expenses'] = self._get_top_expenses(db, user_id, limit=3)

            # Если спрашивают про бюджет
            if any(word in msg_lower for word in ['бюджет', 'лимит', 'превышен']):
                context['budgets'] = self._get_budget_status(db, user_id)

            # Если спрашивают про цели
            if any(word in msg_lower for word in ['цел', 'накопл', 'сберег']):
                context['goals'] = self._get_goals_info(db, user_id)

            # Если спрашивают про инсайты/рекомендации
            if any(word in msg_lower for word in ['совет', 'рекоменд', 'инсайт', 'предупрежд']):
                context['insights'] = self._get_recent_insights(db, user_id)

        return context

    def _build_prompt(self, message: str, context: Dict) -> str:
        """
        Формирует промпт для LLM с контекстом.
        """
        prompt_parts = [
            f"ВОПРОС ПОЛЬЗОВАТЕЛЯ: {message}",
            "",
            "ДАННЫЕ ИЗ БАЗЫ:"
        ]

        # Если есть данные за период
        if 'period_balance' in context:
            pb = context['period_balance']
            prompt_parts.append(
                f"• Баланс за период {pb['period_start']} - {pb['period_end']}: {self._format_amount(pb['balance'])} "
                f"(Доходы: {self._format_amount(pb['income'])}, Расходы: {self._format_amount(pb['expenses'])})"
            )
            # Сравнение с предыдущим периодом
            change_income = pb['income'] - pb['prev_income']
            change_expenses = pb['expenses'] - pb['prev_expenses']
            prompt_parts.append(
                f"• По сравнению с предыдущим периодом: доходы {'выросли' if change_income > 0 else 'снизились'} "
                f"на {self._format_amount(abs(change_income))}, расходы {'выросли' if change_expenses > 0 else 'снизились'} "
                f"на {self._format_amount(abs(change_expenses))}"
            )

            if 'period_expenses_by_category' in context:
                prompt_parts.append("• Расходы по категориям за этот период:")
                for cat in context['period_expenses_by_category'][:5]:
                    prompt_parts.append(f"  - {cat['category']}: {self._format_amount(cat['amount'])}")

            if 'period_top_expenses' in context:
                prompt_parts.append("• Крупнейшие траты за этот период:")
                for t in context['period_top_expenses']:
                    prompt_parts.append(f"  - {t['description']}: {self._format_amount(t['amount'])} ({t['date']})")
        else:
            # Стандартные блоки
            if 'balance' in context:
                bal = context['balance']
                prompt_parts.append(
                    f"• Баланс: {self._format_amount(bal['balance'])} "
                    f"(Доходы: {self._format_amount(bal['income'])}, Расходы: {self._format_amount(bal['expenses'])})"
                )

            if 'expenses_by_category' in context:
                prompt_parts.append("• Расходы по категориям:")
                for cat in context['expenses_by_category'][:5]:
                    prompt_parts.append(f"  - {cat['category']}: {self._format_amount(cat['amount'])}")

            if 'budgets' in context:
                prompt_parts.append("• Состояние бюджетов:")
                for b in context['budgets']:
                    status = "❗ ПРЕВЫШЕН" if b['is_exceeded'] else "✓ в норме"
                    prompt_parts.append(
                        f"  - {b['category']}: {self._format_amount(b['spent'])} из {self._format_amount(b['limit'])} ({status})"
                    )

            if 'goals' in context:
                prompt_parts.append("• Финансовые цели:")
                for g in context['goals']:
                    prompt_parts.append(
                        f"  - {g['name']}: {self._format_amount(g['current'])} из {self._format_amount(g['target'])} ({g['percentage']:.0f}%)"
                    )

            if 'recent_transactions' in context:
                prompt_parts.append("• Последние транзакции:")
                for t in context['recent_transactions']:
                    sign = "+" if t['is_income'] else "-"
                    prompt_parts.append(f"  - {t['date']}: {t['description']} ({sign}{self._format_amount(t['amount'])})")

            if 'top_expenses' in context:
                prompt_parts.append("• Крупнейшие траты:")
                for t in context['top_expenses']:
                    prompt_parts.append(f"  - {t['description']}: {self._format_amount(t['amount'])}")

            if 'insights' in context:
                prompt_parts.append("• Недавние инсайты:")
                for ins in context['insights']:
                    prompt_parts.append(f"  - [{ins['type']}] {ins['title']}: {ins['description']}")

        prompt_parts.append("")
        prompt_parts.append(
            "Если вопрос касается финансов, используй предоставленные данные. "
            "Если вопрос общий (приветствие, как дела и т.п.), просто вежливо ответь и предложи помощь по финансам. "
            "Будь краток (максимум 3-4 предложения)."
        )

        return "\n".join(prompt_parts)

    # === Вспомогательные методы для сбора данных ===

    def _get_balance_info(self, db: Session, user_id: str) -> Dict:
        """Получает информацию об общем балансе."""
        income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == True
        ).scalar() or Decimal('0')

        expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False
        ).scalar() or Decimal('0')

        income = float(Decimal(str(income))) if income else 0.0
        expenses = float(Decimal(str(expenses))) if expenses else 0.0

        return {
            'income': income,
            'expenses': expenses,
            'balance': income - expenses
        }

    def _get_recent_transactions(self, db: Session, user_id: str, limit: int = 5) -> List[Dict]:
        """Получает последние транзакции."""
        txns = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(desc(Transaction.date)).limit(limit).all()

        return [{
            'date': t.date.strftime('%d.%m'),
            'description': t.description[:30],
            'amount': float(t.amount),
            'is_income': t.is_income
        } for t in txns]

    def _get_expenses_by_category(self, db: Session, user_id: str,
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Получает расходы по категориям.
        Если даты не указаны, за текущий месяц.
        """
        if start_date is None:
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        if end_date is None:
            end_date = datetime.now()

        results = db.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Category.name).order_by(desc('total')).all()

        return [{
            'category': r.name,
            'amount': float(r.total) if r.total else 0.0
        } for r in results]

    def _get_top_expenses(self, db: Session, user_id: str, limit: int = 3,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Получает крупнейшие траты.
        Если даты не указаны, за всё время.
        """
        query = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False
        )
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        txns = query.order_by(desc(Transaction.amount)).limit(limit).all()

        return [{
            'description': t.description[:50],
            'amount': float(t.amount),
            'date': t.date.strftime('%d.%m.%Y')
        } for t in txns]

    def _get_budget_status(self, db: Session, user_id: str) -> List[Dict]:
        """Получает статус бюджетов."""
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        budgets = db.query(Budget).filter(Budget.user_id == user_id).all()

        result = []
        for b in budgets:
            spent = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.category_id == b.category_id,
                Transaction.is_income == False,
                Transaction.date >= current_month
            ).scalar() or Decimal('0')

            spent = float(Decimal(str(spent))) if spent else 0.0

            result.append({
                'category': b.category.name if b.category else 'Unknown',
                'limit': float(b.amount),
                'spent': spent,
                'is_exceeded': spent > float(b.amount)
            })

        return result

    def _get_goals_info(self, db: Session, user_id: str) -> List[Dict]:
        """Получает информацию о финансовых целях."""
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()
        return [{
            'name': g.name,
            'target': float(g.target_amount),
            'current': float(g.current_amount),
            'percentage': (float(g.current_amount) / float(g.target_amount) * 100) if g.target_amount > 0 else 0
        } for g in goals]

    def _get_recent_insights(self, db: Session, user_id: str) -> List[Dict]:
        """Получает недавние инсайты."""
        insights = db.query(Insight).filter(
            Insight.user_id == user_id
        ).order_by(desc(Insight.created_at)).limit(5).all()
        return [{
            'type': i.type,
            'title': i.title,
            'description': i.description[:100]
        } for i in insights]


# Глобальный экземпляр агента
chat_agent = ChatAgent()
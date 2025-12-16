from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models import Transaction, Category, Budget, Goal, Insight
from app.services.ollama_client import ollama_client, OllamaError
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class ChatAgent:
    """
    AI ассистент на базе Ollama с доступом к финансовой БД.
    """

    def __init__(self):
        self.system_prompt = self.system_prompt = """Ты - продвинутый финансовый помощник WealthWise с глубоким пониманием личных финансов.

ТВОИ ВОЗМОЖНОСТИ:
- Анализ финансовых паттернов и трендов
- Выявление аномалий и рисков
- Персонализированные рекомендации по экономии
- Прогнозирование будущих расходов
- Помощь в достижении финансовых целей

ПРАВИЛА ОБЩЕНИЯ:
1. Отвечай КРАТКО и КОНКРЕТНО (2-4 предложения)
2. Используй ТОЛЬКО ФАКТЫ из предоставленных данных
3. Форматируй суммы с ₽ и разделителями (например: 15 000 ₽)
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
            # Получаем контекст из БД
            context = self._gather_context(db, user_id, message)

            # Формируем промпт с контекстом
            prompt = self._build_prompt(message, context)

            # Запрашиваем ответ у Ollama
            response = await ollama_client.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.3,  # Низкая температура для фактических ответов
                max_tokens=300  # Ограничиваем длину ответа
            )

            # Постобработка ответа
            response = self._postprocess_response(response)

            return response

        except OllamaError as e:
            logger.error(f"Ollama error: {e}")
            return "Извините, AI ассистент временно недоступен. Попробуйте позже или проверьте, что Ollama запущен."
        except Exception as e:
            logger.error(f"Chat agent error: {e}", exc_info=True)
            return "Произошла ошибка при обработке запроса. Попробуйте переформулировать вопрос."

    def _gather_context(self, db: Session, user_id: str, message: str) -> Dict:
        """
        Собирает релевантный контекст из БД на основе сообщения пользователя.
        """
        msg_lower = message.lower()
        context = {}

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

        # Добавляем релевантный контекст
        if 'balance' in context:
            bal = context['balance']
            prompt_parts.append(
                f"• Баланс: {bal['balance']:,.2f} ₽ (Доходы: {bal['income']:,.2f} ₽, Расходы: {bal['expenses']:,.2f} ₽)")

        if 'expenses_by_category' in context:
            prompt_parts.append("• Расходы по категориям:")
            for cat in context['expenses_by_category'][:5]:  # Топ-5
                prompt_parts.append(f"  - {cat['category']}: {cat['amount']:,.2f} ₽")

        if 'budgets' in context:
            prompt_parts.append("• Состояние бюджетов:")
            for b in context['budgets']:
                status = "❗ ПРЕВЫШЕН" if b['is_exceeded'] else "✓ в норме"
                prompt_parts.append(f"  - {b['category']}: {b['spent']:,.0f} ₽ из {b['limit']:,.0f} ₽ ({status})")

        if 'goals' in context:
            prompt_parts.append("• Финансовые цели:")
            for g in context['goals']:
                prompt_parts.append(
                    f"  - {g['name']}: {g['current']:,.0f} ₽ из {g['target']:,.0f} ₽ ({g['percentage']:.0f}%)")

        if 'recent_transactions' in context:
            prompt_parts.append("• Последние транзакции:")
            for t in context['recent_transactions']:
                sign = "+" if t['is_income'] else "-"
                prompt_parts.append(f"  - {t['date']}: {t['description']} ({sign}{t['amount']:,.0f} ₽)")

        if 'top_expenses' in context:
            prompt_parts.append("• Крупнейшие траты:")
            for t in context['top_expenses']:
                prompt_parts.append(f"  - {t['description']}: {t['amount']:,.0f} ₽")

        if 'insights' in context:
            prompt_parts.append("• Недавние инсайты:")
            for ins in context['insights']:
                prompt_parts.append(f"  - [{ins['type']}] {ins['title']}: {ins['description']}")

        prompt_parts.append("")
        prompt_parts.append(
            "Ответь на вопрос пользователя, используя ТОЛЬКО эти данные. Будь краток (максимум 3-4 предложения).")

        return "\n".join(prompt_parts)

    def _postprocess_response(self, response: str) -> str:
        """
        Постобработка ответа от LLM.
        """
        # Удаляем лишние пробелы
        response = response.strip()

        # Ограничиваем длину (на случай если модель игнорировала инструкции)
        sentences = response.split('.')
        if len(sentences) > 4:
            response = '.'.join(sentences[:4]) + '.'

        return response

    # === Вспомогательные методы для сбора данных ===

    def _get_balance_info(self, db: Session, user_id: str) -> Dict:
        """Получает информацию о балансе"""
        income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == True
        ).scalar() or Decimal('0')

        expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False
        ).scalar() or Decimal('0')

        # ИСПРАВЛЕНИЕ: явное приведение к Decimal
        income = Decimal(str(income)) if income else Decimal('0')
        expenses = Decimal(str(expenses)) if expenses else Decimal('0')

        return {
            'income': float(income),
            'expenses': float(expenses),
            'balance': float(income - expenses)
        }

    def _get_recent_transactions(self, db: Session, user_id: str, limit: int = 5) -> List[Dict]:
        """Получает последние транзакции"""
        txns = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(desc(Transaction.date)).limit(limit).all()

        return [{
            'date': t.date.strftime('%d.%m'),
            'description': t.description[:30],
            'amount': float(t.amount),
            'is_income': t.is_income
        } for t in txns]

    def _get_expenses_by_category(self, db: Session, user_id: str) -> List[Dict]:
        """Получает расходы по категориям за текущий месяц"""
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)

        results = db.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= current_month
        ).group_by(Category.name).order_by(desc('total')).all()

        return [{
            'category': r.name,
            'amount': float(r.total) if r.total else 0.0
        } for r in results]

    def _get_top_expenses(self, db: Session, user_id: str, limit: int = 3) -> List[Dict]:
        """Получает крупнейшие траты"""
        txns = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False
        ).order_by(desc(Transaction.amount)).limit(limit).all()

        return [{
            'description': t.description[:50],
            'amount': float(t.amount),
            'date': t.date.strftime('%d.%m.%Y')
        } for t in txns]

    def _get_budget_status(self, db: Session, user_id: str) -> List[Dict]:
        """Получает статус бюджетов"""
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

            spent = Decimal(str(spent)) if spent else Decimal('0')

            result.append({
                'category': b.category.name if b.category else 'Unknown',
                'limit': float(b.amount),
                'spent': float(spent),
                'is_exceeded': spent > Decimal(str(b.amount))
            })

        return result

    def _get_goals_info(self, db: Session, user_id: str) -> List[Dict]:
        """Получает информацию о финансовых целях"""
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()

        return [{
            'name': g.name,
            'target': float(g.target_amount),
            'current': float(g.current_amount),
            'percentage': (float(g.current_amount) / float(g.target_amount) * 100) if g.target_amount > 0 else 0
        } for g in goals]

    def _get_recent_insights(self, db: Session, user_id: str) -> List[Dict]:
        """Получает недавние инсайты"""
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
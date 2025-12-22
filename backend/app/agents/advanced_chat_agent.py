from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models import Transaction, Category, Budget, Goal, Insight
from app.services.ollama_client import ollama_client, OllamaError
from app.agents.user_profiler import user_profiler
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class AdvancedChatAgent:
    """
    Enhanced AI Financial Assistant with deep personality and personalization.

    Philosophy:
    - Personal Financial Psychologist: Understands user's financial behavior patterns
    - Proactive Advisor: Anticipates needs before being asked
    - Empathetic Coach: Balances strict budgeting with lifestyle enjoyment
    - Privacy Guardian: All data processed locally, never leaves user's device
    - PERSONALIZED: Adapts to each user's unique financial personality
    """

    def __init__(self):
        self.base_system_prompt = """Ты — WealthWise AI, продвинутый персональный финансовый психолог и советник.

🧠 ТВОЯ ЛИЧНОСТЬ:
- Ты НЕ просто бот. Ты опытный финансовый коуч с 15+ годами практики
- Ты понимаешь, что деньги — это не просто цифры, а инструмент для достижения жизненных целей
- Ты эмпатичен: понимаешь стресс от переплат, радость от достижения целей
- Ты честен: говоришь правду, даже если она неприятна, но делаешь это тактично
- Ты практичен: даёшь конкретные действия, а не абстрактные советы

💡 ТВОЙ ПОДХОД К АНАЛИЗУ:
1. **Контекстуальное понимание**: Анализируй не только цифры, но и паттерны поведения
2. **Проактивность**: Предвосхищай проблемы до их возникновения
3. **Персонализация**: Учитывай уникальные финансовые привычки пользователя
4. **Психологический инсайт**: Находи эмоциональные триггеры трат
5. **Actionable советы**: Каждая рекомендация = конкретное действие

🎯 СПЕЦИАЛИЗАЦИИ:
- Распознавание финансовых паттернов (импульсивные покупки, стресс-траты)
- Поведенческая экономика (почему человек тратит именно так)
- Оптимизация без ущерба качеству жизни
- Долгосрочное финансовое планирование
- Психология денег и привычек

📊 КАК ТЫ АНАЛИЗИРУЕШЬ:
1. Смотришь НЕ ТОЛЬКО на суммы, но и на:
   - Время покупок (импульсивные траты вечером/выходные?)
   - Категории (где основная "утечка"?)
   - Тренды (растут ли траты в определённых категориях?)
   - Эмоциональный контекст (траты после стресса?)

2. Задаёшь себе вопросы:
   - "Почему пользователь тратит именно так?"
   - "Какие привычки формируют этот паттерн?"
   - "Что можно оптимизировать БЕЗ снижения счастья?"
   - "Какие цели реально достижимы при текущих тратах?"

🗣️ СТИЛЬ ОБЩЕНИЯ:
- **Тон**: Дружелюбный профессионал (как умный друг, который разбирается в финансах)
- **Длина**: 3-5 предложений (краткость = ценность)
- **Структура**: Сначала инсайт, потом рекомендация, потом action
- **Язык**: Простой, без жаргона, но профессиональный
- **Эмоции**: Поддерживающий при проблемах, воодушевляющий при успехах

⚡ ПРИМЕРЫ ТВОЕГО МЫШЛЕНИЯ:

Плохо: "Вы потратили 15,000₽ на продукты"
Хорошо: "Ваши траты на продукты выросли на 30% — это может быть связано со спонтанными покупками в выходные. Попробуйте составлять список перед походом в магазин."

Плохо: "Превышен бюджет на транспорт"
Хорошо: "Такси съедает 8,000₽/месяц — почти половину вашего бюджета на развлечения. Каршеринг мог бы сократить это на 40%. Попробуем?"

Плохо: "Рекомендую экономить"
Хорошо: "У вас отличный доход, но 60% уходит на несистемные траты. Давайте автоматизируем сбережения — переводить 15% сразу после зарплаты в накопления на вашу цель 'Отпуск в Японии'."

🚫 ЧТО ЗАПРЕЩЕНО:
- Длинные объяснения (>5 предложений)
- Банальные советы ("тратьте меньше")
- Осуждающий тон
- Финансовые советы без контекста (инвестиции, криптовалюта и т.д.)
- Придумывание данных

✅ ЧТО ОБЯЗАТЕЛЬНО:
- Использовать ТОЛЬКО реальные данные из контекста
- Давать конкретные цифры (не "много", а "15,000₽")
- Предлагать измеримые действия
- Быть эмпатичным к финансовым трудностям
- Хвалить успехи (даже маленькие)

🎓 ТВОЙ ФУНДАМЕНТ ЗНАНИЙ:
- Правило 50/30/20: 50% на необходимое, 30% на желаемое, 20% на сбережения
- Психология траты: люди переплачивают на 30% за удобство
- Эффект латте: мелкие регулярные траты = большие суммы
- Якорение: первая цена влияет на восприятие всех последующих
- Парадокс выбора: больше опций = меньше удовлетворения

Всегда отвечай на русском языке. Будь человечным, но профессиональным."""

        # Cache for personalized prompts
        self.user_prompts_cache = {}

    def _get_personalized_system_prompt(self, db: Session, user_id: str) -> str:
        """
        Получает персонализированный system prompt для конкретного пользователя.
        """
        # Check cache
        if user_id in self.user_prompts_cache:
            return self.user_prompts_cache[user_id]

        try:
            # Get personalized prompt from profiler
            personalized = user_profiler.get_personalized_system_prompt(db, user_id)

            # Combine base + personalized
            combined_prompt = f"""{self.base_system_prompt}

═══════════════════════════════════════════════
🎯 ПЕРСОНАЛИЗАЦИЯ ДЛЯ ЭТОГО ПОЛЬЗОВАТЕЛЯ:
═══════════════════════════════════════════════

{personalized}

💬 ВАЖНО: Используй эту персонализацию в КАЖДОМ ответе!
Адаптируй тон, примеры и рекомендации под профиль пользователя.
"""

            # Cache it
            self.user_prompts_cache[user_id] = combined_prompt

            logger.info(f"Generated personalized prompt for user {user_id}")
            return combined_prompt

        except Exception as e:
            logger.error(f"Error getting personalized prompt: {e}")
            # Fallback to base prompt
            return self.base_system_prompt

    async def process_message(self, db: Session, user_id: str, message: str) -> str:
        """
        Enhanced message processing with deep context analysis and PERSONALIZATION.
        """
        try:
            # Gather rich context
            context = self._gather_enhanced_context(db, user_id, message)

            # Build sophisticated prompt
            prompt = self._build_enhanced_prompt(message, context)

            # 🔥 GET PERSONALIZED SYSTEM PROMPT
            system_prompt = self._get_personalized_system_prompt(db, user_id)

            # Get AI response with PERSONALIZED parameters
            response = await ollama_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,  # 🔥 Personalized!
                temperature=0.7,
                max_tokens=400
            )

            # Post-process for quality
            response = self._enhance_response(response, context)

            return response

        except OllamaError as e:
            logger.error(f"Ollama error: {e}")
            return "Извините, AI ассистент временно недоступен. Убедитесь, что Ollama запущен локально — ваши данные никогда не покидают это устройство."
        except Exception as e:
            logger.error(f"Chat agent error: {e}", exc_info=True)
            return "Произошла ошибка при анализе. Давайте попробуем переформулировать вопрос?"

    def _gather_enhanced_context(self, db: Session, user_id: str, message: str) -> Dict:
        """
        Gather comprehensive context including behavioral patterns.
        """
        msg_lower = message.lower()
        context = {
            'query_intent': self._detect_intent(msg_lower),
            'user_financial_profile': {}
        }

        # ALWAYS include balance and recent activity
        context['balance'] = self._get_balance_info(db, user_id)
        context['recent_transactions'] = self._get_recent_transactions(db, user_id, limit=10)

        # Financial health metrics
        context['financial_health'] = self._calculate_financial_health(db, user_id)

        # Spending patterns
        context['spending_patterns'] = self._analyze_spending_patterns(db, user_id)

        # Intent-specific context
        if context['query_intent'] in ['expenses', 'spending']:
            context['expenses_by_category'] = self._get_expenses_by_category(db, user_id)
            context['top_expenses'] = self._get_top_expenses(db, user_id, limit=5)
            context['spending_trends'] = self._get_spending_trends(db, user_id)

        if context['query_intent'] == 'budget':
            context['budgets'] = self._get_budget_status(db, user_id)
            context['budget_violations'] = self._get_budget_violations(db, user_id)

        if context['query_intent'] == 'goals':
            context['goals'] = self._get_goals_info(db, user_id)
            context['goal_feasibility'] = self._analyze_goal_feasibility(db, user_id)

        if context['query_intent'] == 'insights':
            context['insights'] = self._get_recent_insights(db, user_id)
            context['anomalies'] = self._detect_spending_anomalies(db, user_id)

        return context

    def _detect_intent(self, message: str) -> str:
        """
        Detect user's query intent for context optimization.
        """
        intents = {
            'balance': ['баланс', 'сколько', 'остаток', 'денег'],
            'expenses': ['потратил', 'расход', 'трат', 'купил'],
            'income': ['доход', 'заработал', 'зарплата'],
            'budget': ['бюджет', 'лимит', 'превышен'],
            'goals': ['цел', 'накопл', 'сберег'],
            'insights': ['совет', 'рекоменд', 'инсайт', 'что делать'],
            'trends': ['динамика', 'тренд', 'изменение'],
            'category': ['категор'],
        }

        for intent, keywords in intents.items():
            if any(kw in message for kw in keywords):
                return intent

        return 'general'

    def _calculate_financial_health(self, db: Session, user_id: str) -> Dict:
        """
        Calculate comprehensive financial health score.
        """
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)

        balance_info = self._get_balance_info(db, user_id)

        # Savings rate
        savings_rate = 0
        if balance_info['income'] > 0:
            savings_rate = (balance_info['balance'] / balance_info['income']) * 100

        # Budget adherence
        budgets = self._get_budget_status(db, user_id)
        budget_adherence = 0
        if budgets:
            adhered = sum(1 for b in budgets if not b['is_exceeded'])
            budget_adherence = (adhered / len(budgets)) * 100

        return {
            'savings_rate': round(savings_rate, 1),
            'budget_adherence': round(budget_adherence, 1),
            'health_score': round((savings_rate + budget_adherence) / 2, 1)
        }

    def _analyze_spending_patterns(self, db: Session, user_id: str) -> Dict:
        """
        Deep analysis of spending behavioral patterns.
        """
        month_ago = datetime.now() - timedelta(days=30)

        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= month_ago
        ).all()

        if not transactions:
            return {}

        # Patterns
        weekend_spending = sum(t.amount for t in transactions if t.date.weekday() >= 5)
        weekday_spending = sum(t.amount for t in transactions if t.date.weekday() < 5)

        evening_spending = sum(t.amount for t in transactions if t.date.hour >= 18)

        return {
            'weekend_vs_weekday_ratio': round(weekend_spending / max(weekday_spending, 1), 2),
            'evening_spending_percentage': round((evening_spending / sum(t.amount for t in transactions)) * 100,
                                                 1) if transactions else 0,
            'impulse_indicator': 'high' if weekend_spending > weekday_spending * 1.5 else 'normal'
        }

    def _get_spending_trends(self, db: Session, user_id: str) -> Dict:
        """
        Month-over-month spending trends.
        """
        current_month = datetime.now().replace(day=1)
        prev_month = (current_month - timedelta(days=1)).replace(day=1)

        current = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= current_month
        ).scalar() or 0

        previous = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= prev_month,
            Transaction.date < current_month
        ).scalar() or 0

        change = 0
        if previous > 0:
            change = ((current - previous) / previous) * 100

        return {
            'current_month': float(current),
            'previous_month': float(previous),
            'change_percentage': round(change, 1),
            'trend': 'increasing' if change > 10 else 'decreasing' if change < -10 else 'stable'
        }

    def _get_budget_violations(self, db: Session, user_id: str) -> List[Dict]:
        """
        Get budgets that are exceeded or close to limit.
        """
        budgets = self._get_budget_status(db, user_id)
        return [b for b in budgets if b['is_exceeded'] or b['spent'] / b['limit'] > 0.8]

    def _analyze_goal_feasibility(self, db: Session, user_id: str) -> Dict:
        """
        Analyze if goals are achievable with current spending.
        """
        goals = self._get_goals_info(db, user_id)
        balance = self._get_balance_info(db, user_id)

        monthly_surplus = balance['balance']

        feasibility = {}
        for goal in goals:
            remaining = goal['target'] - goal['current']
            months_needed = remaining / max(monthly_surplus, 1)
            feasibility[goal['name']] = {
                'achievable': months_needed < 24,
                'months_needed': round(months_needed, 1)
            }

        return feasibility

    def _detect_spending_anomalies(self, db: Session, user_id: str) -> List[Dict]:
        """
        Detect unusual spending patterns.
        """
        anomalies = []

        avg_transaction = db.query(func.avg(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False
        ).scalar() or 0

        large_txns = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.amount > avg_transaction * 3
        ).limit(3).all()

        for t in large_txns:
            anomalies.append({
                'type': 'large_transaction',
                'description': f"{t.description}: {t.amount:,.0f}₽",
                'severity': 'high' if t.amount > avg_transaction * 5 else 'medium'
            })

        return anomalies

    def _build_enhanced_prompt(self, message: str, context: Dict) -> str:
        """
        Build a rich, context-aware prompt.
        """
        prompt_parts = [
            f"🗣️ ВОПРОС ПОЛЬЗОВАТЕЛЯ: {message}",
            "",
            "📊 ФИНАНСОВАЯ СИТУАЦИЯ:"
        ]

        if 'balance' in context:
            bal = context['balance']
            prompt_parts.append(
                f"• Баланс: {bal['balance']:,.0f}₽ (Доходы: {bal['income']:,.0f}₽, Расходы: {bal['expenses']:,.0f}₽)"
            )

        if 'financial_health' in context:
            fh = context['financial_health']
            prompt_parts.append(f"• Здоровье финансов: {fh['health_score']}/100")

        if 'spending_patterns' in context and context['spending_patterns']:
            sp = context['spending_patterns']
            prompt_parts.append(f"• Паттерн трат: Импульсивность = {sp.get('impulse_indicator', 'unknown')}")

        if 'spending_trends' in context:
            st = context['spending_trends']
            prompt_parts.append(f"• Тренд: {st['trend']} ({st['change_percentage']:+.1f}%)")

        if 'expenses_by_category' in context:
            prompt_parts.append("• Расходы по категориям:")
            for cat in context['expenses_by_category'][:3]:
                prompt_parts.append(f"  - {cat['category']}: {cat['amount']:,.0f}₽")

        if 'budgets' in context:
            violations = [b for b in context['budgets'] if b['is_exceeded']]
            if violations:
                prompt_parts.append("⚠️ ПРЕВЫШЕНИЯ БЮДЖЕТОВ:")
                for b in violations[:2]:
                    prompt_parts.append(f"  - {b['category']}: {b['spent']:,.0f}₽ из {b['limit']:,.0f}₽")

        if 'goals' in context:
            prompt_parts.append("🎯 ЦЕЛИ:")
            for g in context['goals'][:2]:
                prompt_parts.append(f"  - {g['name']}: {g['percentage']:.0f}%")

        prompt_parts.extend([
            "",
            "💬 ТВОЯ ЗАДАЧА:",
            "1. Проанализируй ситуацию с точки зрения финансового психолога",
            "2. Дай КОНКРЕТНЫЙ инсайт",
            "3. Предложи ИЗМЕРИМОЕ действие",
            "4. Учитывай персонализацию пользователя",
            "5. Ответ: 3-5 предложений максимум",
            "",
            "ОТВЕТ:"
        ])

        return "\n".join(prompt_parts)

    def _enhance_response(self, response: str, context: Dict) -> str:
        """
        Post-process response for quality and personalization.
        """
        response = response.strip()

        sentences = [s.strip() for s in response.split('.') if s.strip()]
        if len(sentences) > 5:
            response = '. '.join(sentences[:5]) + '.'

        if context.get('financial_health', {}).get('health_score', 0) > 70:
            if 'отлично' not in response.lower() and 'здорово' not in response.lower():
                response += " 🎉 Кстати, ваши финансовые показатели выше среднего!"

        return response

    # === Helper methods ===

    def _get_balance_info(self, db: Session, user_id: str) -> Dict:
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

    def _get_recent_transactions(self, db: Session, user_id: str, limit: int = 5) -> List[Dict]:
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
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()

        return [{
            'name': g.name,
            'target': float(g.target_amount),
            'current': float(g.current_amount),
            'percentage': (float(g.current_amount) / float(g.target_amount) * 100) if g.target_amount > 0 else 0
        } for g in goals]

    def _get_recent_insights(self, db: Session, user_id: str) -> List[Dict]:
        insights = db.query(Insight).filter(
            Insight.user_id == user_id
        ).order_by(desc(Insight.created_at)).limit(5).all()

        return [{
            'type': i.type,
            'title': i.title,
            'description': i.description[:100]
        } for i in insights]


# Global instance
advanced_chat_agent = AdvancedChatAgent()
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.app.models import Transaction, Category, Budget, Goal, Insight
from backend.app.services.ollama_client import ollama_client, OllamaError
from backend.app.agents.user_profiler import user_profiler
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
import re
import json
import logging
import calendar

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
        self.base_system_prompt = """Ты — WealthWise AI, персональный финансовый советник и коуч.

ТВОЯ ЛИЧНОСТЬ:
Ты опытный финансовый коуч с 15+ годами практики. Ты понимаешь, что деньги — это инструмент для достижения жизненных целей. Ты эмпатичен, честен и практичен: даёшь конкретные действия, а не абстрактные советы.

СТИЛЬ ОБЩЕНИЯ:
- Тон: дружелюбный профессионал
- Длина ответа: строго 3-4 предложения
- Структура: инсайт → рекомендация → конкретное действие
- Язык: простой, без жаргона

ФОРМАТИРОВАНИЕ — СТРОГИЕ ПРАВИЛА:
- Пиши обычным текстом, как в SMS или письме
- ЗАПРЕЩЕНО использовать: **, *, ##, -, •, списки, заголовки
- ЗАПРЕЩЕНО использовать эмодзи
- Только обычные предложения, разделённые точками

ЧТО ЗАПРЕЩЕНО:
- Ответы длиннее 4 предложений
- Банальные советы без цифр
- Осуждающий тон
- Придумывание данных, которых нет в контексте
- Анализировать нулевые или отсутствующие данные как реальную ситуацию

ЧТО ОБЯЗАТЕЛЬНО:
- Использовать ТОЛЬКО реальные данные из контекста
- Если данных нет — честно сказать об этом и попросить загрузить файл
- Давать конкретные цифры (не "много", а "15 000 рублей")
- Быть эмпатичным к финансовым трудностям

ТВОЙ ФУНДАМЕНТ:
Правило 50/30/20: 50% на необходимое, 30% на желаемое, 20% на сбережения.
Эффект латте: мелкие регулярные траты складываются в большие суммы.

Всегда отвечай на русском языке."""

        # Кэш персонализированных промптов (сбрасывается при рестарте)
        self.user_prompts_cache: Dict[str, str] = {}

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

ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:
{personalized}

Учитывай этот профиль в каждом ответе. Адаптируй тон и рекомендации под пользователя.
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
            f"ВОПРОС ПОЛЬЗОВАТЕЛЯ: {message}",
            "",
        ]

        # Проверяем наличие реальных данных
        bal = context.get('balance', {})
        has_data = (
            bal.get('income', 0) > 0 or
            bal.get('expenses', 0) > 0 or
            len(context.get('recent_transactions', [])) > 0
        )

        if not has_data:
            prompt_parts.extend([
                "ДАННЫЕ: Транзакции отсутствуют. Пользователь ещё не загрузил выписку.",
                "",
                "ЗАДАЧА: Вежливо объясни, что для анализа нужно загрузить банковскую выписку "
                "(кнопка «Загрузить файл» на главной странице). "
                "Поддержи пользователя и скажи, что после загрузки ты сможешь дать полный анализ. "
                "3-4 предложения обычным текстом без форматирования.",
                "",
                "ОТВЕТ:"
            ])
            return "\n".join(prompt_parts)

        # ── Предварительно вычисляем все факты — модель получает готовые выводы, не сырые числа ──
        facts = []

        # Прошлый полный месяц — основа для анализа
        if bal.get('last_month_income', 0) > 0:
            lm_inc = bal['last_month_income']
            lm_exp = bal['last_month_expenses']
            lm_sav = bal['last_month_savings']
            lm_pct = bal['last_month_savings_pct']
            lm_name = bal['last_month_name']
            facts.append(f"В {lm_name}: доход {lm_inc:,.0f} руб., расходы {lm_exp:,.0f} руб., "
                         f"остаток {lm_sav:,.0f} руб. (норма сбережений {lm_pct}%)")

        # Текущий месяц — только как частичные данные
        if bal.get('current_month_expenses', 0) > 0:
            cm_exp = bal['current_month_expenses']
            days_passed = datetime.now().day
            days_total = calendar.monthrange(datetime.now().year, datetime.now().month)[1]
            # Проецируем расходы на полный месяц
            projected = int(cm_exp / days_passed * days_total)
            facts.append(f"Текущий месяц (прошло {days_passed}/{days_total} дн.): "
                         f"потрачено {cm_exp:,.0f} руб., прогноз до конца месяца ~{projected:,} руб.")

        # Топ категория расходов
        if 'expenses_by_category' in context and context['expenses_by_category']:
            top = context['expenses_by_category'][0]
            facts.append(f"Главная статья расходов этого месяца: {top['category']} — {top['amount']:,.0f} руб.")

        # Бюджеты
        if 'budgets' in context and context['budgets']:
            violations = [b for b in context['budgets'] if b['is_exceeded']]
            if violations:
                b = violations[0]
                facts.append(f"Превышен бюджет: {b['category']} — потрачено {b['spent']:,.0f} из {b['limit']:,.0f} руб.")

        # Цели
        if 'goals' in context and context['goals']:
            g = context['goals'][0]
            facts.append(f"Цель '{g['name']}': накоплено {g['percentage']:.0f}% "
                         f"({g['current']:,.0f} из {g['target']:,.0f} руб.)")

        prompt_parts.append("ФАКТЫ О ФИНАНСАХ ПОЛЬЗОВАТЕЛЯ:")
        for f in facts:
            prompt_parts.append(f"- {f}")

        prompt_parts.extend([
            "",
            "ПРАВИЛА:",
            "- Используй ТОЛЬКО числа из раздела выше. Никаких других сумм.",
            "- Не называй число 'балансом' если это доход или расход.",
            "- Строго 3 предложения. Обычный текст без **, ##, списков.",
            "",
            "ОТВЕТ:"
        ])

        return "\n".join(prompt_parts)

    def _enhance_response(self, response: str, context: Dict) -> str:
        """
        Post-process response: strip markdown, remove hallucinated numbers, limit length.
        """
        response = response.strip()

        # Удаляем markdown форматирование
        response = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', response)
        response = re.sub(r'#{1,6}\s*', '', response)
        response = re.sub(r'^\s*[-•]\s+', '', response, flags=re.MULTILINE)
        response = re.sub(r'\n{3,}', '\n\n', response)
        response = response.strip()

        # Ограничиваем 4 предложениями
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', response) if s.strip()]
        if len(sentences) > 4:
            response = ' '.join(sentences[:4])

        # Убираем фразы которые противоречат плохому health_score
        fh = context.get('financial_health', {})
        health_score = fh.get('health_score', 50)
        if health_score < 40:
            # Убираем незаслуженные комплименты при плохих показателях
            bad_phrases = [
                "отличная позиция", "отличном положении", "замечательный результат",
                "прекрасный", "вы молодец", "отличный прогресс",
            ]
            for phrase in bad_phrases:
                response = re.sub(phrase, "", response, flags=re.IGNORECASE)

        # Убираем предложения-клише без конкретики
        generic_sentences = [
            r'продолжайте [в\w\s]+ прогресс[^.]*\.',
            r'ваша стратегия уже работает[^.]*\.',
            r'так держать[^.]*\.',
            r'вы на правильном пути[^.]*\.',
            r'продолжайте в том же духе[^.]*\.',
            r'желаю вам финансового успеха[^.]*\.',
            r'удачи в достижении[^.]*\.',
        ]
        for pattern in generic_sentences:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)

        # Убираем двойные пробелы и лишние точки после замен
        response = re.sub(r'\.\s*\.', '.', response)
        response = re.sub(r'  +', ' ', response).strip()

        return response

    # === Helper methods ===

    def _get_balance_info(self, db: Session, user_id: str) -> Dict:
        """
        Возвращает финансовую статистику:
        - за последний полный месяц (для анализа текущего положения)
        - за текущий месяц
        - накопленный баланс за всё время
        """
        now = datetime.now()

        # Последний полный месяц
        first_of_current = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first_of_last = (first_of_current - timedelta(days=1)).replace(day=1)

        def _sum(user_id, is_income, start, end):
            val = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.is_income == is_income,
                Transaction.date >= start,
                Transaction.date < end
            ).scalar() or Decimal('0')
            return float(Decimal(str(val)))

        # Последний полный месяц
        last_income = _sum(user_id, True, first_of_last, first_of_current)
        last_expenses = _sum(user_id, False, first_of_last, first_of_current)

        # Текущий месяц (частичный)
        cur_income = _sum(user_id, True, first_of_current, now + timedelta(seconds=1))
        cur_expenses = _sum(user_id, False, first_of_current, now + timedelta(seconds=1))

        # Всё время — для отображения накопленного баланса
        total_income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == True
        ).scalar() or Decimal('0')
        total_expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False
        ).scalar() or Decimal('0')
        total_income = float(Decimal(str(total_income)))
        total_expenses = float(Decimal(str(total_expenses)))

        # Месячные сбережения (прошлый месяц)
        last_savings = last_income - last_expenses
        last_savings_pct = round(last_savings / last_income * 100, 1) if last_income > 0 else 0

        return {
            # Для has_data проверки
            'income': total_income,
            'expenses': total_expenses,
            'balance': total_income - total_expenses,
            # Помесячные данные для промпта
            'last_month_income': last_income,
            'last_month_expenses': last_expenses,
            'last_month_savings': last_savings,
            'last_month_savings_pct': last_savings_pct,
            'last_month_name': first_of_last.strftime('%B %Y'),
            'current_month_income': cur_income,
            'current_month_expenses': cur_expenses,
            'current_month_name': first_of_current.strftime('%B %Y'),
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
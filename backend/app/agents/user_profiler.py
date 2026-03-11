from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.app.models import Transaction, Category, Budget, Goal
from datetime import datetime, timedelta
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class UserProfiler:
    """
    Собирает и анализирует финансовые привычки пользователя для персонализации AI.

    Создает "финансовый профиль" пользователя который используется для:
    1. Персонализированных промптов
    2. Fine-tuning модели (в будущем)
    3. Адаптивных рекомендаций
    """

    def build_user_profile(self, db: Session, user_id: str) -> Dict:
        """
        Создает полный финансовый профиль пользователя.
        """
        profile = {
            'user_id': user_id,
            'generated_at': datetime.now().isoformat(),
            'financial_behavior': self._analyze_behavior(db, user_id),
            'spending_patterns': self._analyze_spending_patterns(db, user_id),
            'preferences': self._extract_preferences(db, user_id),
            'goals_mindset': self._analyze_goals_mindset(db, user_id),
            'risk_profile': self._assess_risk_profile(db, user_id),
            'personalization_data': self._prepare_training_data(db, user_id)
        }

        # Сохраняем профиль для использования в промптах
        self._save_profile(db, user_id, profile)

        logger.info(f"Built user profile for {user_id}")
        return profile

    def _analyze_behavior(self, db: Session, user_id: str) -> Dict:
        """
        Анализ финансового поведения пользователя.
        """
        last_90_days = datetime.now() - timedelta(days=90)

        txns = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.date >= last_90_days
        ).all()

        if not txns:
            return {'profile_type': 'new_user', 'data_points': 0}

        # Основные метрики
        total_income = sum(t.amount for t in txns if t.is_income)
        total_expenses = sum(t.amount for t in txns if not t.is_income)
        avg_transaction = total_expenses / len([t for t in txns if not t.is_income]) if txns else 0

        # Частота трат
        days_with_spending = len(set(t.date.date() for t in txns if not t.is_income))
        spending_frequency = days_with_spending / 90 if days_with_spending > 0 else 0

        # Тип поведения
        savings_rate = (total_income - total_expenses) / total_income if total_income > 0 else 0

        if savings_rate > 0.3:
            behavior_type = "saver"  # Накопитель
        elif savings_rate > 0.1:
            behavior_type = "balanced"  # Сбалансированный
        else:
            behavior_type = "spender"  # Транжира

        return {
            'profile_type': behavior_type,
            'savings_rate': round(savings_rate, 2),
            'spending_frequency': round(spending_frequency, 2),
            'avg_transaction': round(float(avg_transaction), 2),
            'data_points': len(txns),
            'time_range_days': 90
        }

    def _analyze_spending_patterns(self, db: Session, user_id: str) -> Dict:
        """
        Глубокий анализ паттернов трат для персонализации.
        """
        last_60_days = datetime.now() - timedelta(days=60)

        txns = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= last_60_days
        ).all()

        if not txns:
            return {}

        # Временные паттерны
        morning = [t for t in txns if 6 <= t.date.hour < 12]
        afternoon = [t for t in txns if 12 <= t.date.hour < 18]
        evening = [t for t in txns if 18 <= t.date.hour < 24]
        night = [t for t in txns if 0 <= t.date.hour < 6]

        weekday = [t for t in txns if t.date.weekday() < 5]
        weekend = [t for t in txns if t.date.weekday() >= 5]

        # Категории предпочтений
        category_spending = {}
        for t in txns:
            if t.category:
                cat_name = t.category.name
                category_spending[cat_name] = category_spending.get(cat_name, 0) + float(t.amount)

        top_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:3]

        # Импульсивность
        large_txns = [t for t in txns if t.amount > 5000]
        impulse_score = len(large_txns) / len(txns) if txns else 0

        return {
            'time_preferences': {
                'morning': len(morning),
                'afternoon': len(afternoon),
                'evening': len(evening),
                'night': len(night),
                'dominant_time': max([
                    ('morning', len(morning)),
                    ('afternoon', len(afternoon)),
                    ('evening', len(evening)),
                    ('night', len(night))
                ], key=lambda x: x[1])[0]
            },
            'day_preferences': {
                'weekday_spending': sum(t.amount for t in weekday),
                'weekend_spending': sum(t.amount for t in weekend),
                'weekend_premium': round(
                    (sum(t.amount for t in weekend) / max(sum(t.amount for t in weekday), 1)),
                    2
                )
            },
            'top_categories': [{'category': cat, 'amount': amt} for cat, amt in top_categories],
            'impulse_score': round(impulse_score, 2),
            'impulse_level': 'high' if impulse_score > 0.1 else 'medium' if impulse_score > 0.05 else 'low'
        }

    def _extract_preferences(self, db: Session, user_id: str) -> Dict:
        """
        Извлекает явные предпочтения пользователя из его действий.
        """
        # Бюджеты = что важно для пользователя
        budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
        budget_categories = [b.category.name for b in budgets if b.category]

        # Цели = к чему стремится
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()
        goal_targets = [
            {
                'name': g.name,
                'target': float(g.target_amount),
                'priority': 'high' if g.target_amount > 100000 else 'medium'
            }
            for g in goals
        ]

        return {
            'budget_focus_areas': budget_categories,
            'financial_goals': goal_targets,
            'goal_oriented': len(goals) > 0,
            'budget_conscious': len(budgets) > 0
        }

    def _analyze_goals_mindset(self, db: Session, user_id: str) -> Dict:
        """
        Анализирует подход пользователя к финансовым целям.
        """
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()

        if not goals:
            return {'mindset': 'no_goals', 'planning_horizon': 'none'}

        # Анализ горизонта планирования
        total_target = sum(float(g.target_amount) for g in goals)
        avg_target = total_target / len(goals)

        if avg_target > 500000:
            mindset = "long_term_planner"  # Долгосрочное планирование
        elif avg_target > 100000:
            mindset = "mid_term_focused"  # Среднесрочные цели
        else:
            mindset = "short_term_achiever"  # Краткосрочные достижения

        # Прогресс выполнения
        goals_with_progress = [g for g in goals if g.current_amount > 0]
        completion_rate = len(goals_with_progress) / len(goals) if goals else 0

        return {
            'mindset': mindset,
            'total_goals': len(goals),
            'avg_goal_size': round(avg_target, 2),
            'active_pursuit': completion_rate > 0.5,
            'completion_rate': round(completion_rate, 2)
        }

    def _assess_risk_profile(self, db: Session, user_id: str) -> Dict:
        """
        Оценивает склонность к финансовым рискам.
        """
        last_90_days = datetime.now() - timedelta(days=90)

        txns = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.date >= last_90_days
        ).all()

        if not txns:
            return {'risk_level': 'unknown'}

        # Показатели риска
        total_spent = sum(t.amount for t in txns)
        large_txns = [t for t in txns if t.amount > total_spent * 0.1]  # >10% от общих трат

        # Бюджетная дисциплина
        budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
        current_month = datetime.now().replace(day=1)

        budget_violations = 0
        for budget in budgets:
            spent = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.category_id == budget.category_id,
                Transaction.is_income == False,
                Transaction.date >= current_month
            ).scalar() or 0

            if spent > budget.amount:
                budget_violations += 1

        violation_rate = budget_violations / len(budgets) if budgets else 0

        # Определение профиля риска
        if violation_rate > 0.5 or len(large_txns) > 5:
            risk_level = "high"
        elif violation_rate > 0.2 or len(large_txns) > 2:
            risk_level = "moderate"
        else:
            risk_level = "low"

        return {
            'risk_level': risk_level,
            'budget_violations': budget_violations,
            'large_transactions_count': len(large_txns),
            'financial_discipline': 'high' if risk_level == 'low' else 'medium' if risk_level == 'moderate' else 'low'
        }

    def _prepare_training_data(self, db: Session, user_id: str) -> Dict:
        """
        Подготавливает данные для fine-tuning модели.

        Формат: примеры диалогов + контекст пользователя
        """
        profile_summary = {
            'behavior': self._analyze_behavior(db, user_id).get('profile_type', 'unknown'),
            'spending_patterns': self._analyze_spending_patterns(db, user_id),
            'preferences': self._extract_preferences(db, user_id),
            'goals_mindset': self._analyze_goals_mindset(db, user_id).get('mindset', 'unknown'),
            'risk_profile': self._assess_risk_profile(db, user_id).get('risk_level', 'unknown')
        }

        # Генерируем персонализированный system prompt
        personalized_prompt = self._generate_personalized_prompt(profile_summary)

        return {
            'profile_summary': profile_summary,
            'personalized_system_prompt': personalized_prompt,
            'ready_for_finetuning': True
        }

    def _generate_personalized_prompt(self, profile: Dict) -> str:
        """
        Генерирует персонализированный system prompt на основе профиля.
        """
        behavior = profile.get('behavior', 'balanced')
        mindset = profile.get('goals_mindset', 'unknown')
        risk = profile.get('risk_profile', 'moderate')

        # Базовый шаблон
        prompt_parts = [
            "Ты — персональный финансовый психолог этого пользователя.",
            "",
            "ПРОФИЛЬ КЛИЕНТА:"
        ]

        # Адаптация под тип поведения
        if behavior == 'saver':
            prompt_parts.append("• Тип: НАКОПИТЕЛЬ (откладывает >30% дохода)")
            prompt_parts.append("• Подход: Хвали дисциплину, помогай оптимизировать инвестиции")
        elif behavior == 'spender':
            prompt_parts.append("• Тип: ТРАНЖИРА (откладывает <10% дохода)")
            prompt_parts.append("• Подход: Будь честным но поддерживающим, фокус на маленьких шагах")
        else:
            prompt_parts.append("• Тип: СБАЛАНСИРОВАННЫЙ (откладывает 10-30%)")
            prompt_parts.append("• Подход: Помогай найти баланс между жизнью и накоплениями")

        # Адаптация под цели
        if mindset == 'long_term_planner':
            prompt_parts.append("• Цели: Долгосрочное планирование (крупные цели)")
            prompt_parts.append("• Стиль: Стратегический, говори о сложных процентах и инвестициях")
        elif mindset == 'short_term_achiever':
            prompt_parts.append("• Цели: Краткосрочные достижения")
            prompt_parts.append("• Стиль: Мотивируй быстрыми победами, празднуй маленькие успехи")

        # Адаптация под риск
        if risk == 'high':
            prompt_parts.append("• Риск-профиль: ВЫСОКИЙ (импульсивные траты, нарушения бюджета)")
            prompt_parts.append("• Тактика: Мягко напоминай о последствиях, предлагай защитные механизмы")
        elif risk == 'low':
            prompt_parts.append("• Риск-профиль: НИЗКИЙ (дисциплинирован)")
            prompt_parts.append("• Тактика: Предлагай продвинутые стратегии оптимизации")

        prompt_parts.extend([
            "",
            "АДАПТИРУЙ СВОИ ОТВЕТЫ:",
            "1. Учитывай этот профиль в каждом совете",
            "2. Говори на языке, который резонирует с этим типом личности",
            "3. Предлагай решения, соответствующие уровню дисциплины",
            "4. Хвали прогресс в контексте их профиля"
        ])

        return "\n".join(prompt_parts)

    def _save_profile(self, db: Session, user_id: str, profile: Dict):
        """
        Сохраняет профиль пользователя для быстрого доступа.
        """
        # TODO: Сохранить в таблицу user_profiles или в JSON файл
        # Пока логируем
        logger.info(f"User profile for {user_id}: {profile['financial_behavior']['profile_type']}")

        # В будущем: сохранение в БД или файл для fine-tuning
        # profile_path = f"data/user_profiles/{user_id}.json"
        # with open(profile_path, 'w') as f:
        #     json.dump(profile, f, indent=2)

    def get_personalized_system_prompt(self, db: Session, user_id: str) -> str:
        """
        Получает персонализированный system prompt для пользователя.
        """
        profile = self.build_user_profile(db, user_id)
        return profile['personalization_data']['personalized_system_prompt']


# Global instance
user_profiler = UserProfiler()
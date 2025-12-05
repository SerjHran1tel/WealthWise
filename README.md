# WealthWise: Документация структуры проекта

## Backend

### `/backend/app/main.py`
**Назначение:** Главный файл FastAPI приложения, точка входа для всех API запросов.

**Содержимое:**
- Инициализация FastAPI приложения
- CORS настройки для работы с frontend
- Подключение роутеров (endpoints)
- Middleware для логирования и обработки ошибок
- Startup/shutdown события (инициализация БД, загрузка моделей)
- Health check endpoint

**Endpoints:**
- `GET /` - Health check
- `GET /api/health` - Статус системы
- Подключение роутеров из других модулей

**Зависимости:** FastAPI, uvicorn, python-multipart

---

### `/backend/app/models.py`
**Назначение:** SQLAlchemy ORM модели для работы с базой данных.

**Модели:**

1. **Transaction** (Транзакция)
   - `id` (UUID, primary key)
   - `user_id` (UUID, для мультиюзерности)
   - `date` (DateTime)
   - `description` (String) - описание операции
   - `amount` (Decimal) - сумма
   - `currency` (String, default='RUB')
   - `category_id` (Foreign Key)
   - `subcategory` (String, nullable)
   - `tags` (JSON, массив тегов)
   - `is_income` (Boolean) - доход или расход
   - `account` (String) - счёт/карта
   - `created_at` (DateTime)
   - `updated_at` (DateTime)

2. **Category** (Категория)
   - `id` (UUID, primary key)
   - `name` (String, unique) - название
   - `type` (Enum: expense/income)
   - `icon` (String) - иконка для UI
   - `color` (String) - цвет в hex
   - `parent_id` (Foreign Key, nullable) - для подкатегорий
   - `keywords` (JSON) - ключевые слова для автокатегоризации

3. **Budget** (Бюджет)
   - `id` (UUID, primary key)
   - `user_id` (UUID)
   - `category_id` (Foreign Key)
   - `amount` (Decimal) - лимит
   - `period` (Enum: monthly/weekly/yearly)
   - `start_date` (Date)
   - `end_date` (Date, nullable)
   - `is_active` (Boolean)

4. **Goal** (Финансовая цель)
   - `id` (UUID, primary key)
   - `user_id` (UUID)
   - `name` (String) - название цели
   - `target_amount` (Decimal)
   - `current_amount` (Decimal)
   - `deadline` (Date, nullable)
   - `category_id` (Foreign Key, nullable) - связанная категория
   - `created_at` (DateTime)
   - `achieved` (Boolean)

5. **Insight** (Инсайт/Рекомендация)
   - `id` (UUID, primary key)
   - `user_id` (UUID)
   - `type` (Enum: anomaly/recommendation/warning/info)
   - `title` (String)
   - `description` (Text)
   - `priority` (Integer, 1-5)
   - `related_category` (Foreign Key, nullable)
   - `data` (JSON) - дополнительные данные для визуализации
   - `is_read` (Boolean)
   - `created_at` (DateTime)

6. **UserPreference** (Настройки пользователя)
   - `id` (UUID, primary key)
   - `user_id` (UUID, unique)
   - `currency` (String)
   - `language` (String)
   - `notification_enabled` (Boolean)
   - `auto_categorization` (Boolean)
   - `learning_enabled` (Boolean) - дообучение на данных пользователя

**Связи:**
- Transaction → Category (many-to-one)
- Budget → Category (many-to-one)
- Goal → Category (many-to-one)
- Category → Category (self-referential для подкатегорий)

---

### `/backend/app/schemas.py`
**Назначение:** Pydantic схемы для валидации данных API.

**Схемы:**

1. **TransactionCreate / TransactionUpdate / TransactionResponse**
   - Валидация входящих данных
   - Форматирование ответов API

2. **CategoryCreate / CategoryResponse**

3. **BudgetCreate / BudgetResponse**

4. **GoalCreate / GoalResponse**

5. **FileUpload**
   - `file_type` (Enum: csv/pdf)
   - `bank_format` (String) - Сбербанк, Тинькофф и т.д.

6. **AnalyticsRequest**
   - `start_date` (Date)
   - `end_date` (Date)
   - `categories` (List[UUID], optional)
   - `group_by` (Enum: day/week/month/category)

7. **ChatMessage**
   - `message` (String)
   - `context` (Dict, optional) - контекст для AI

**Validators:**
- Проверка дат (start_date < end_date)
- Проверка сумм (amount > 0)
- Нормализация строк (удаление пробелов)

---

### `/backend/app/database.py`
**Назначение:** Настройка подключения к SQLite базе данных.

**Содержимое:**
- Создание engine для SQLAlchemy
- Настройка SessionLocal (фабрика сессий)
- Base для ORM моделей
- Функция `get_db()` - dependency для FastAPI endpoints
- Функция `init_db()` - создание таблиц и начальных данных
- Функция `seed_categories()` - заполнение дефолтными категориями

**Путь к БД:** `data/wealthwise.db`

**Настройки:**
- SQLite с поддержкой JSON
- Включить foreign keys
- WAL mode для производительности

---

### `/backend/app/agents/classifier.py`
**Назначение:** Агент категоризации транзакций (RAG + ML).

**Класс:** `ClassifierAgent`

**Методы:**

1. `__init__()`
   - Загрузка ML модели
   - Инициализация векторной БД (ChromaDB/FAISS)
   - Загрузка embedding модели

2. `categorize_transaction(description: str, amount: float) -> Category`
   - Главный метод категоризации
   - Процесс:
     1. Создать эмбеддинг описания
     2. Поиск похожих в векторной БД (топ-5)
     3. Если similarity > 0.9 → использовать категорию
     4. Иначе применить rule-based правила
     5. Иначе использовать ML классификатор
     6. Возврат категории с confidence score

3. `learn_from_correction(transaction_id: UUID, correct_category: UUID)`
   - Обучение на исправлениях пользователя
   - Добавление в векторную БД
   - Обновление весов модели (incremental learning)

4. `add_rule(pattern: str, category: UUID)`
   - Добавление нового правила категоризации

5. `get_similar_transactions(description: str, top_k: int = 5) -> List[Transaction]`
   - Поиск похожих транзакций для RAG

**Правила (rule-based):**
- Регулярные выражения для банков, магазинов
- Ключевые слова по категориям
- Приоритет: точное совпадение → частичное → ML

**ML модель:**
- TF-IDF + LogisticRegression или RandomForest
- Обучена на датасете финансовых транзакций
- Сохранена в `models/classifier/`

---

### `/backend/app/agents/analytics.py`
**Назначение:** Агент анализа трат и выявления паттернов.

**Класс:** `AnalyticsAgent`

**Методы:**

1. `get_spending_by_category(start_date, end_date, user_id) -> Dict`
   - Группировка расходов по категориям
   - Возврат суммы, процента, количества транзакций

2. `get_spending_trend(category_id, period: str, user_id) -> List[Dict]`
   - Тренд расходов по времени
   - period: 'daily', 'weekly', 'monthly'
   - Возврат временного ряда

3. `detect_anomalies(user_id, period: str = 'month') -> List[Insight]`
   - Выявление аномальных трат
   - Метод: Z-score или IQR
   - Сравнение с историческими данными
   - Генерация инсайтов типа "anomaly"

4. `compare_periods(user_id, period1, period2) -> Dict`
   - Сравнение двух периодов
   - Процентное изменение по категориям
   - Топ изменений (biggest_increase, biggest_decrease)

5. `find_recurring_payments(user_id) -> List[Dict]`
   - Поиск регулярных платежей и подписок
   - Анализ по описанию и сумме
   - Определение периодичности (monthly, yearly)

6. `calculate_statistics(user_id, category_id=None) -> Dict`
   - Статистика: среднее, медиана, стд. отклонение
   - По всем тратам или конкретной категории

**Алгоритмы:**
- Pandas для агрегаций
- NumPy/SciPy для статистики
- Выявление аномалий: метод межквартильного размаха (IQR)

---

### `/backend/app/agents/forecast.py`
**Назначение:** Агент прогнозирования будущих расходов.

**Класс:** `ForecastAgent`

**Методы:**

1. `forecast_next_month(user_id) -> Dict[category_id, predicted_amount]`
   - Прогноз расходов на следующий месяц по категориям
   - Метод: Moving Average или простая линейная регрессия
   - Учёт сезонности

2. `predict_goal_achievement(goal_id) -> Dict`
   - Прогноз достижения цели
   - Возврат: вероятность, предполагаемая дата, нужная экономия
   - Расчёт на основе текущего темпа накоплений

3. `forecast_budget_overflow(user_id, budget_id) -> Dict`
   - Предсказание превышения бюджета
   - Warning если прогноз > 90% лимита
   - Рекомендации по корректировке

4. `seasonal_analysis(user_id, category_id) -> Dict`
   - Анализ сезонности трат
   - Выявление паттернов по месяцам/кварталам

**Модели прогнозирования:**
- Простые: Moving Average, Exponential Smoothing
- Продвинутые (опционально): ARIMA, Prophet
- Для MVP достаточно простых методов

---

### `/backend/app/agents/advisor.py`
**Назначение:** Агент генерации рекомендаций и советов.

**Класс:** `AdvisorAgent`

**Методы:**

1. `generate_recommendations(user_id) -> List[Insight]`
   - Главный метод генерации рекомендаций
   - Анализ всех паттернов
   - Создание списка инсайтов с приоритетами

2. `find_savings_opportunities(user_id) -> List[Insight]`
   - Поиск возможностей для экономии
   - Примеры:
     - "Вы тратите 15% на доставку еды. Можно сэкономить готовя дома"
     - "Такси стоит 8000₽/мес. Рассмотрите каршеринг"

3. `detect_unused_subscriptions(user_id) -> List[Insight]`
   - Поиск неиспользуемых подписок
   - Логика: регулярный платеж без связанных расходов
   - Пример: "Подписка Netflix 999₽, последний вход 2 месяца назад"

4. `suggest_budget_adjustments(user_id) -> List[Insight]`
   - Рекомендации по корректировке бюджетов
   - На основе фактических трат

5. `generate_weekly_report(user_id) -> Dict`
   - Еженедельный отчёт
   - Структура: summary, top_spendings, insights, actions

**Логика рекомендаций:**
- Rule-based система
- Шаблоны с подстановкой данных
- Приоритизация по влиянию на бюджет

---

### `/backend/app/agents/orchestrator.py`
**Назначение:** Координатор всех агентов и обработчик чат-запросов.

**Класс:** `Orchestrator`

**Атрибуты:**
- `classifier: ClassifierAgent`
- `analytics: AnalyticsAgent`
- `forecast: ForecastAgent`
- `advisor: AdvisorAgent`
- `llm: LocalLLM` (опционально для чата)

**Методы:**

1. `process_chat_message(user_id, message: str) -> str`
   - Обработка сообщений из чата
   - Определение интента (что хочет пользователь)
   - Вызов нужного агента
   - Форматирование ответа

2. `analyze_transactions(user_id, transactions: List[Transaction])`
   - Оркестрация анализа новых транзакций
   - Последовательность:
     1. Категоризация (classifier)
     2. Выявление аномалий (analytics)
     3. Проверка бюджетов (forecast)
     4. Генерация рекомендаций (advisor)

3. `generate_insights(user_id) -> List[Insight]`
   - Генерация всех инсайтов
   - Агрегация от всех агентов
   - Приоритизация и фильтрация

4. `schedule_weekly_report(user_id)`
   - Планирование еженедельного отчёта
   - Вызов advisor.generate_weekly_report()
   - Сохранение в БД или отправка уведомления

**Интент-классификация для чата:**
- "Сколько я потратил на X?" → analytics
- "Прогноз на следующий месяц?" → forecast
- "Как мне сэкономить?" → advisor
- "Покажи аномалии" → analytics

---

### `/backend/app/services/parser.py`
**Назначение:** Парсинг CSV и PDF выписок от разных банков.

**Функции:**

1. `detect_bank_format(file_content: bytes) -> str`
   - Автоопределение формата банка
   - Анализ заголовков CSV или структуры PDF
   - Возврат: 'sberbank', 'tinkoff', 'alpha', 'generic'

2. `parse_csv(file_path: str, bank_format: str) -> List[Dict]`
   - Парсинг CSV выписки
   - Маппинг колонок под разные банки
   - Возврат списка транзакций (сырые данные)

3. `parse_pdf(file_path: str) -> List[Dict]`
   - Извлечение текста из PDF (PyPDF2 или pdfplumber)
   - Парсинг структуры выписки
   - Более сложная логика (таблицы, форматы)

4. `normalize_transaction(raw_data: Dict, bank_format: str) -> Dict`
   - Нормализация данных под единую схему
   - Парсинг дат, сумм, описаний
   - Определение is_income (доход/расход)

5. `deduplicate_transactions(existing: List, new: List) -> List`
   - Удаление дубликатов
   - Сравнение по дате + сумме + описание

**Форматы банков:**

**Сбербанк CSV:**
```
Дата операции;Дата списания;Категория;Описание операции;Сумма операции;Валюта
```

**Тинькофф CSV:**
```
Дата операции;Дата платежа;Категория;Описание;Сумма платежа;Валюта платежа
```

**Альфа-Банк CSV:**
```
Дата;Описание;Сумма;Валюта;Категория
```

**Generic CSV (универсальный):**
```
Date,Description,Amount,Currency
```

---

### `/backend/app/services/categorizer.py`
**Назначение:** Сервисный слой для категоризации (обёртка над ClassifierAgent).

**Функции:**

1. `categorize_bulk(transactions: List[Transaction], user_id: UUID) -> List[Transaction]`
   - Массовая категоризация транзакций
   - Использует ClassifierAgent
   - Батчинг для производительности

2. `suggest_category(description: str) -> List[Tuple[Category, float]]`
   - Предложение категорий с вероятностями
   - Для UI (пользователь выбирает из топ-3)

3. `update_categorization_rules(user_id: UUID)`
   - Обновление персональных правил
   - На основе исправлений пользователя

---

### `/backend/app/services/analyzer.py`
**Назначение:** Сервисный слой аналитики (обёртка над AnalyticsAgent).

**Функции:**

1. `get_dashboard_data(user_id: UUID, period: str) -> Dict`
   - Данные для главного дашборда
   - Агрегация метрик: total_spent, by_category, trends

2. `get_category_breakdown(user_id: UUID, start_date, end_date) -> Dict`
   - Детальная разбивка по категориям
   - Для визуализации pie/bar charts

3. `export_report(user_id: UUID, format: str) -> bytes`
   - Экспорт отчёта (CSV, PDF, Excel)
   - Генерация документа с аналитикой

---

### `/backend/app/utils/helpers.py`
**Назначение:** Вспомогательные утилиты.

**Функции:**

1. `format_currency(amount: Decimal, currency: str = 'RUB') -> str`
   - Форматирование суммы для отображения
   - "1234.56" → "1 234,56 ₽"

2. `parse_date(date_string: str) -> datetime`
   - Парсинг дат из разных форматов
   - Поддержка DD.MM.YYYY, YYYY-MM-DD, и др.

3. `calculate_percentage_change(old_value, new_value) -> float`
   - Расчёт процентного изменения

4. `get_period_bounds(period: str) -> Tuple[datetime, datetime]`
   - Получение границ периода
   - 'this_month' → (start_of_month, end_of_month)
   - 'last_week', 'last_30_days' и т.д.

---

## API Endpoints (в main.py или отдельных роутерах)

### Транзакции
- `POST /api/transactions/upload` - Загрузка CSV/PDF
- `GET /api/transactions` - Список транзакций (с фильтрами)
- `GET /api/transactions/{id}` - Одна транзакция
- `PUT /api/transactions/{id}` - Обновление (категория, теги)
- `DELETE /api/transactions/{id}` - Удаление
- `POST /api/transactions/bulk-categorize` - Массовая категоризация

### Категории
- `GET /api/categories` - Список категорий
- `POST /api/categories` - Создание категории
- `PUT /api/categories/{id}` - Обновление
- `DELETE /api/categories/{id}` - Удаление

### Аналитика
- `GET /api/analytics/dashboard` - Данные дашборда
- `GET /api/analytics/spending-by-category` - Расходы по категориям
- `GET /api/analytics/trends` - Тренды
- `GET /api/analytics/comparison` - Сравнение периодов

### Инсайты
- `GET /api/insights` - Список инсайтов
- `PUT /api/insights/{id}/read` - Отметить прочитанным
- `POST /api/insights/generate` - Сгенерировать новые

### Бюджеты и цели
- `GET /api/budgets` - Список бюджетов
- `POST /api/budgets` - Создать бюджет
- `GET /api/goals` - Список целей
- `POST /api/goals` - Создать цель

### Чат
- `POST /api/chat` - Отправить сообщение AI
- `GET /api/chat/history` - История чата

### Отчёты
- `GET /api/reports/weekly` - Еженедельный отчёт
- `GET /api/reports/export` - Экспорт данных

---

## Frontend

### `/frontend/src/App.js`
**Назначение:** Главный компонент приложения, роутинг.

**Содержимое:**
- React Router настройка
- Layout (Header, Sidebar, Content)
- Роуты страниц:
  - `/` - Dashboard
  - `/transactions` - Список транзакций
  - `/upload` - Загрузка файлов
  - `/analytics` - Аналитика
  - `/goals` - Цели и бюджеты
  - `/chat` - Чат с AI
  - `/settings` - Настройки

**State Management:**
- Context для глобальных данных (user, categories)
- Local state для компонентов

---

### `/frontend/src/components/Dashboard/Dashboard.jsx`
**Назначение:** Главная страница с обзором финансов.

**Компоненты:**
- `SummaryCards` - карточки с метриками (всего потрачено, баланс, экономия)
- `SpendingChart` - график расходов по времени
- `CategoryBreakdown` - распределение по категориям (pie chart)
- `RecentTransactions` - последние транзакции
- `InsightsPanel` - важные инсайты и рекомендации

**API запросы:**
- `GET /api/analytics/dashboard`
- `GET /api/insights`

---

### `/frontend/src/components/Upload/FileUpload.jsx`
**Назначение:** Страница загрузки выписок.

**Функциональность:**
- Drag-and-drop зона для файлов
- Выбор файла через file picker
- Выбор формата банка (если не автоопределяется)
- Progress bar загрузки
- Предпросмотр распарсенных транзакций
- Подтверждение импорта

**API запросы:**
- `POST /api/transactions/upload`

**Состояния:**
- idle, uploading, processing, preview, success, error

---

### `/frontend/src/components/Transactions/TransactionList.jsx`
**Назначение:** Список всех транзакций с фильтрами.

**Функциональность:**
- Таблица транзакций (дата, описание, категория, сумма)
- Фильтры:
  - По датам (date range picker)
  - По категориям (multiselect)
  - По типу (доход/расход)
  - Поиск по описанию
- Сортировка по колонкам
- Pagination или виртуальный скролл
- Редактирование категории inline
- Добавление тегов
- Удаление транзакций

**Компоненты:**
- `TransactionRow` - строка таблицы
- `CategorySelector` - выбор категории
- `FilterPanel` - панель фильтров

**API запросы:**
- `GET /api/transactions`
- `PUT /api/transactions/{id}`
- `DELETE /api/transactions/{id}`

---

### `/frontend/src/components/Charts/SpendingChart.jsx`
**Назначение:** График расходов по времени.

**Библиотека:** Recharts

**Типы графиков:**
- Line chart - тренд расходов
- Area chart - накопленные расходы
- Bar chart - по месяцам

**Props:**
- `data` - массив {date, amount, category}
- `groupBy` - day/week/month
- `categories` - фильтр по категориям

---

### `/frontend/src/components/Charts/CategoryPieChart.jsx`
**Назначение:** Круговая диаграмма расходов по категориям.

**Библиотека:** Recharts

**Функциональность:**
- Интерактивная диаграмма
- Hover для деталей
- Клик для перехода к транзакциям категории

---

### `/frontend/src/components/Chat/ChatInterface.jsx`
**Назначение:** Интерфейс чата с AI-помощником.

**Компоненты:**
- `MessageList` - список сообщений
- `MessageBubble` - пузырёк сообщения (user/ai)
- `ChatInput` - поле ввода с кнопкой отправки

**Функциональность:**
- История чата
- Автоскролл к новым сообщениям
- Typing indicator когда AI думает
- Быстрые вопросы (кнопки с примерами)
- Markdown рендеринг в ответах AI

**API запросы:**
- `POST /api/chat`
- `GET /api/chat/history`

---

### `/frontend/src/components/Goals/GoalsPanel.jsx`
**Назначение:** Управление финансовыми целями.

**Компоненты:**
- `GoalCard` - карточка цели с прогресс-баром
- `CreateGoalModal` - модалка создания цели
- `BudgetList` - список бюджетов

**Функциональность:**
- Отображение прогресса целей
- Создание/редактирование целей
- Визуализация достижения
- Связь с категориями

**API запросы:**
- `GET /api/goals`
- `POST /api/goals`
- `PUT /api/goals/{id}`

---

### `/frontend/src/components/Insights/InsightCard.jsx`
**Назначение:** Карточка инсайта/рекомендации.

**Props:**
- `type` - anomaly/recommendation/warning
- `title` - заголовок
- `description` - описание
- `priority` - важность
- `actionable` - есть ли действие

**Функциональность:**
- Иконка по типу
- Цвет по приоритету
- Кнопка действия (если есть)
- Отметить прочитанным

---

### `/frontend/src/services/api.js`
**Назначение:** Централизованный API клиент.

**Содержимое:**
- Axios instance с базовым URL
- Функции для всех API endpoints
- Обработка ошибок
- Interceptors для loading states

**Примеры функций:**
```javascript
export const api = {
  transactions: {
    getAll: (params) => axios.get('/api/transactions', { params }),
    upload: (file, format) => axios.post('/api/transactions/upload', formData),
    update: (id, data) => axios.put(`/api/transactions/${id}`, data),
    delete: (id) => axios.delete(`/api/transactions/${id}`)
  },
  analytics: {
    getDashboard: (period) => axios.get('/api/analytics/dashboard', { params: { period } }),
    getSpendingByCategory: (start, end) => axios.get('/api/analytics/spending-by-category', { params })
  },
  chat: {
    sendMessage: (message) => axios.post('/api/chat', { message }),
    getHistory: () => axios.get('/api/chat/history')
  }
}
```

---

## Дополнительные файлы

### `/backend/requirements.txt`
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
pandas==2.1.3
numpy==1.26.2
scikit-learn==1.3.2
sentence-transformers==2.2.2
chromadb==0.4.18
python-multipart==0.0.6
python-dateutil==2.8.2
PyPDF2==3.0.1
openpyxl==3.1.2
```

### `/frontend/package.json`
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "recharts": "^2.10.3",
    "date-fns": "^2.30.0",
    "tailwindcss": "^3.3.5"
  }
}
```

### `/frontend/tailwind.config.js`
**Назначение:** Конфигурация Tailwind CSS.

**Содержимое:**
```javascript
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6',
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
        income: '#10B981',
        expense: '#EF4444'
      }
    }
  },
  plugins: []
}
```

---

## Модели ML

### `/models/embeddings/`
**Назначение:** Хранилище предобученной embedding модели.

**Модель:** `sentence-transformers/all-MiniLM-L6-v2`
- Размер: ~22MB
- Размерность векторов: 384
- Язык: multilingual (включая русский)

**Файлы:**
- `config.json` - конфигурация модели
- `pytorch_model.bin` - веса модели
- `tokenizer.json` - токенизатор

**Использование:**
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('models/embeddings/')
embedding = model.encode("Покупка в Пятёрочке")
```

---

### `/models/classifier/`
**Назначение:** Обученный классификатор категорий.

**Файлы:**
- `model.pkl` - сериализованная scikit-learn модель
- `vectorizer.pkl` - TF-IDF векторизатор
- `label_encoder.pkl` - кодировщик категорий
- `metadata.json` - метаданные обучения

**Структура metadata.json:**
```json
{
  "model_type": "RandomForestClassifier",
  "training_date": "2024-01-15",
  "accuracy": 0.87,
  "n_samples": 50000,
  "categories": ["Продукты", "Транспорт", "Развлечения", ...],
  "features": ["tfidf", "amount_log", "hour", "day_of_week"]
}
```

**Обучение модели:**
- Датасет: размеченные транзакции (~50k примеров)
- Фичи: TF-IDF описания + сумма + время
- Модель: RandomForest или LogisticRegression
- Валидация: 80/20 split, cross-validation

---

## Векторная БД

### `/backend/data/vectors/`
**Назначение:** Хранилище векторных представлений транзакций для RAG.

**Используемая БД:** ChromaDB (embedded mode)

**Коллекции:**

1. **transactions_embeddings**
   - Эмбеддинги описаний транзакций
   - Метаданные: category_id, amount, date, user_id
   - Используется для поиска похожих

2. **categorization_rules**
   - Векторы правил категоризации
   - Метаданные: pattern, category_id, priority

**Операции:**
```python
import chromadb

client = chromadb.PersistentClient(path="data/vectors/")
collection = client.get_or_create_collection("transactions_embeddings")

# Добавление
collection.add(
    embeddings=[embedding],
    documents=[description],
    metadatas=[{"category_id": cat_id, "user_id": user_id}],
    ids=[transaction_id]
)

# Поиск похожих
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    where={"user_id": user_id}
)
```

---

## Конфигурация и переменные окружения

### `/backend/.env`
**Назначение:** Переменные окружения для backend.

**Содержимое:**
```env
# Database
DATABASE_URL=sqlite:///./data/wealthwise.db

# Application
APP_NAME=WealthWise
DEBUG=True
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# ML Models
EMBEDDING_MODEL_PATH=models/embeddings/
CLASSIFIER_MODEL_PATH=models/classifier/
VECTOR_DB_PATH=data/vectors/

# Features
ENABLE_RAG=True
ENABLE_LLM=False  # Для MVP отключено
AUTO_CATEGORIZATION=True

# Rate Limiting
MAX_UPLOAD_SIZE_MB=50
MAX_TRANSACTIONS_PER_UPLOAD=10000
```

---

### `/frontend/.env`
**Назначение:** Переменные окружения для frontend.

**Содержимое:**
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_NAME=WealthWise
REACT_APP_VERSION=0.1.0
```

---

## Документация

### `/docs/API.md`
**Назначение:** Полная документация API для разработчиков.

**Содержимое:**

```markdown
# WealthWise API Documentation

## Authentication
В MVP версии аутентификация не требуется (single user).
В будущем: JWT tokens.

## Базовый URL
`http://localhost:8000/api`

## Endpoints

### Транзакции

#### POST /transactions/upload
Загрузка выписки из банка.

**Request:**
- Content-Type: multipart/form-data
- Body:
  - file: File (CSV или PDF)
  - bank_format: string (optional) - 'sberbank', 'tinkoff', 'alpha', 'generic'

**Response:**
```json
{
  "status": "success",
  "imported": 145,
  "duplicates": 3,
  "errors": 0,
  "transactions": [...]
}
```

[... и так далее для всех endpoints ...]
```

---

### `/docs/ARCHITECTURE.md`
**Назначение:** Архитектурная документация проекта.

**Содержимое:**

```markdown
# WealthWise Architecture

## Overview
WealthWise - локальное приложение для анализа личных финансов с использованием AI.

## High-Level Architecture

```

```

## Data Flow

### 1. Transaction Upload Flow
```
User uploads CSV → Parser detects format → Parse & normalize
→ Deduplicate → Categorize (Classifier Agent) → Save to DB
→ Trigger analytics → Generate insights → Return to frontend
```

### 2. Categorization Flow (RAG)
```
New transaction → Create embedding → Search similar in Vector DB
→ If similarity > 0.9: Use same category
→ Else: Apply rules → If no match: ML classifier
→ Return category + confidence
```

### 3. Chat Query Flow
```
User message → Orchestrator → Classify intent
→ Route to appropriate agent → Agent processes
→ Format response → Return to user
```

## Technology Stack

**Backend:**
- FastAPI - web framework
- SQLAlchemy - ORM
- Pandas - data processing
- scikit-learn - ML
- sentence-transformers - embeddings
- ChromaDB - vector database

**Frontend:**
- React 18 - UI framework
- Recharts - data visualization
- Tailwind CSS - styling
- Axios - HTTP client

**ML Models:**
- all-MiniLM-L6-v2 - embeddings (22MB)
- RandomForest/LogisticRegression - classification

## Design Decisions

### Why Local Processing?
- **Privacy**: Financial data never leaves device
- **Cost**: No API costs for AI
- **Speed**: No network latency
- **Offline**: Works without internet

### Why Multi-Agent System?
- **Separation of Concerns**: Each agent has clear responsibility
- **Maintainability**: Easy to update one agent without affecting others
- **Scalability**: Can add new agents easily
- **Testability**: Each agent can be tested independently

### Why RAG for Categorization?
- **Personalization**: Learns from user's corrections
- **Accuracy**: Uses similar past examples
- **Explainability**: Can show why category was chosen
- **Efficiency**: Fast lookup vs. retraining model

## Database Schema

[Detailed schema from models.py]

## Security Considerations

**Data Storage:**
- SQLite with encryption (SQLCipher)
- Vector DB stored locally
- No cloud backups by default

**Input Validation:**
- All API inputs validated with Pydantic
- File upload size limits
- SQL injection protection via ORM

## Performance Optimization

**Backend:**
- Connection pooling for DB
- Batch processing for categorization
- Caching frequent queries
- Async operations where possible

**Frontend:**
- Lazy loading components
- Virtual scrolling for large lists
- Debounced search/filters
- Memoization of heavy computations

## Deployment

**Development:**
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm start
```

**Production:**
- Electron app (desktop)
- Docker container (self-hosted)
- PWA (web version)
```

---

## Дополнительные компоненты

### `/backend/app/routers/`
**Назначение:** Организация API endpoints по модулям.

**Файлы:**

#### `transactions.py`
```python
from fastapi import APIRouter, Depends, UploadFile

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.post("/upload")
async def upload_transactions(file: UploadFile, ...):
    """Загрузка выписки"""
    pass

@router.get("/")
async def get_transactions(skip: int = 0, limit: int = 100, ...):
    """Получить список транзакций"""
    pass

@router.put("/{transaction_id}")
async def update_transaction(transaction_id: UUID, ...):
    """Обновить транзакцию"""
    pass
```

#### `analytics.py`
```python
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/dashboard")
async def get_dashboard_data(period: str = "month", ...):
    """Данные для дашборда"""
    pass

@router.get("/spending-by-category")
async def get_spending_by_category(start_date: date, end_date: date, ...):
    """Расходы по категориям"""
    pass
```

#### `chat.py`
```python
router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/")
async def send_message(message: ChatMessage, ...):
    """Отправить сообщение в чат"""
    pass
```

---

### `/backend/app/core/`
**Назначение:** Ядро приложения - конфигурация, безопасность.

#### `config.py`
**Содержимое:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "WealthWise"
    debug: bool = True
    database_url: str = "sqlite:///./data/wealthwise.db"
    
    # ML Models
    embedding_model_path: str = "models/embeddings/"
    classifier_model_path: str = "models/classifier/"
    vector_db_path: str = "data/vectors/"
    
    # Features
    enable_rag: bool = True
    enable_llm: bool = False
    auto_categorization: bool = True
    
    # Limits
    max_upload_size_mb: int = 50
    max_transactions_per_upload: int = 10000
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### `logging_config.py`
**Содержимое:**
```python
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )
```

---

### `/backend/tests/`
**Назначение:** Unit и integration тесты.

**Структура:**
```
tests/
├── __init__.py
├── test_parser.py          # Тесты парсера
├── test_classifier.py      # Тесты категоризации
├── test_analytics.py       # Тесты аналитики
├── test_api.py            # Тесты API endpoints
└── fixtures/
    ├── sample_sberbank.csv
    ├── sample_tinkoff.csv
    └── test_data.json
```

**Пример test_parser.py:**
```python
import pytest
from app.services.parser import parse_csv, detect_bank_format

def test_detect_sberbank_format():
    with open('fixtures/sample_sberbank.csv', 'rb') as f:
        content = f.read()
    assert detect_bank_format(content) == 'sberbank'

def test_parse_sberbank_csv():
    transactions = parse_csv('fixtures/sample_sberbank.csv', 'sberbank')
    assert len(transactions) > 0
    assert 'date' in transactions[0]
    assert 'amount' in transactions[0]
```

---

### `/frontend/src/hooks/`
**Назначение:** Кастомные React хуки.

#### `useTransactions.js`
```javascript
import { useState, useEffect } from 'react';
import { api } from '../services/api';

export const useTransactions = (filters = {}) => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTransactions = async () => {
      setLoading(true);
      try {
        const data = await api.transactions.getAll(filters);
        setTransactions(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [filters]);

  return { transactions, loading, error };
};
```

#### `useAnalytics.js`
```javascript
export const useAnalytics = (period = 'month') => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      const result = await api.analytics.getDashboard(period);
      setData(result);
      setLoading(false);
    };

    fetchAnalytics();
  }, [period]);

  return { data, loading };
};
```

---

### `/frontend/src/contexts/`
**Назначение:** React Context для глобального состояния.

#### `AppContext.js`
```javascript
import React, { createContext, useState, useEffect } from 'react';
import { api } from '../services/api';

export const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [categories, setCategories] = useState([]);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Загрузка категорий при инициализации
    api.categories.getAll().then(setCategories);
  }, []);

  const value = {
    categories,
    user,
    setUser
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
```

---

### `/frontend/src/utils/`
**Назначение:** Вспомогательные функции для frontend.

#### `formatters.js`
```javascript
export const formatCurrency = (amount, currency = 'RUB') => {
  const symbols = { RUB: '₽', USD: ', EUR: '€' };
  return `${amount.toLocaleString('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })} ${symbols[currency] || currency}`;
};

export const formatDate = (date) => {
  return new Date(date).toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

export const formatPercentage = (value) => {
  return `${(value * 100).toFixed(1)}%`;
};
```

#### `constants.js`
```javascript
export const CATEGORY_ICONS = {
  'Продукты': '🛒',
  'Транспорт': '🚗',
  'Развлечения': '🎬',
  'Рестораны': '🍽️',
  'Здоровье': '💊',
  'Образование': '📚',
  'Одежда': '👕',
  'Подписки': '📱',
  'Дом': '🏠',
  'Другое': '📦'
};

export const PERIOD_OPTIONS = [
  { value: 'week', label: 'Неделя' },
  { value: 'month', label: 'Месяц' },
  { value: 'quarter', label: 'Квартал' },
  { value: 'year', label: 'Год' }
];
```

---

## README файлы

### `/README.md`
**Назначение:** Главный README проекта.

```markdown
# WealthWise - AI-аналитик личных финансов

WealthWise - это локальное приложение для анализа личных финансовых операций с использованием искусственного интеллекта. Все данные обрабатываются на вашем устройстве - полная приватность гарантирована.

## Возможности

- 📊 Автоматическая категоризация транзакций с использованием AI
- 📈 Детальная аналитика расходов и доходов
- 🎯 Постановка финансовых целей и отслеживание прогресса
- 💡 Умные рекомендации по оптимизации бюджета
- 🔮 Прогнозирование будущих расходов
- 💬 Чат с AI-помощником для ответов на вопросы
- 🔒 100% локальная обработка - ваши данные не покидают устройство

## Технологии

**Backend:** Python, FastAPI, SQLAlchemy, scikit-learn, sentence-transformers
**Frontend:** React, Recharts, Tailwind CSS
**AI:** Локальные ML модели, RAG, мультиагентная система

## Установка

### Требования
- Python 3.10+
- Node.js 18+
- 4GB RAM минимум

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## Использование

1. Запустите backend и frontend
2. Откройте http://localhost:3000
3. Загрузите CSV выписку из вашего банка
4. Система автоматически категоризирует транзакции
5. Изучите аналитику и получите рекомендации

## Поддерживаемые форматы банков

- Сбербанк
- Тинькофф
- Альфа-Банк
- Универсальный CSV (Date, Description, Amount)

## Архитектура

Проект использует мультиагентную архитектуру:
- **Classifier Agent** - категоризация транзакций
- **Analytics Agent** - анализ данных и выявление паттернов
- **Forecast Agent** - прогнозирование расходов
- **Advisor Agent** - генерация рекомендаций
- **Orchestrator** - координация всех агентов

## Лицензия

MIT

## Вклад в проект

Pull requests приветствуются! Для крупных изменений сначала откройте issue.
```

---

### `/backend/README.md`
```markdown
# WealthWise Backend

FastAPI приложение для обработки финансовых данных.

## Структура

- `app/` - основной код приложения
- `app/agents/` - AI агенты
- `app/services/` - бизнес-логика
- `models/` - ML модели
- `data/` - база данных и векторное хранилище

## API Documentation

После запуска приложения документация доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск
uvicorn app.main:app --reload

# Тесты
pytest

# Форматирование кода
black app/
```

import csv
import io
from datetime import datetime
from typing import List, Dict


def parse_date(date_str: str) -> datetime:
    """Пытается распарсить дату из разных форматов"""
    # Очищаем строку от лишних пробелов
    date_str = date_str.strip()
    formats = [
        "%d.%m.%Y",  # 10.12.2025
        "%Y-%m-%d",  # 2025-12-10
        "%d/%m/%Y",  # 10/12/2025
        "%d-%m-%Y",  # 10-12-2025
        "%Y.%m.%d"  # 2025.12.10
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    # Если не смогли распарсить, кидаем ошибку, чтобы видеть это в логах
    raise ValueError(f"Cannot parse date: {date_str}")


def parse_csv(file_content: bytes) -> List[Dict]:
    content_str = file_content.decode("utf-8")

    print(f"--- PARSING CSV START ---")
    print(f"File content preview:\n{content_str[:100]}...")

    file_obj = io.StringIO(content_str)

    # Пытаемся определить разделитель (точка с запятой или запятая)
    dialect = csv.Sniffer().sniff(content_str[:1024], delimiters=";,")
    file_obj.seek(0)
    reader = csv.reader(file_obj, delimiter=dialect.delimiter)

    transactions = []

    # Читаем первую строку
    first_row = next(reader, None)
    if not first_row:
        return []

    # Проверка: есть ли заголовок?
    # Если в первой строке есть цифры в начале (похоже на дату), значит заголовка нет
    has_header = False
    try:
        # Пытаемся распарсить первое поле первой строки как дату
        parse_date(first_row[0])
        # Если получилось - значит это данные, возвращаем курсор назад
        file_obj.seek(0)
        reader = csv.reader(file_obj, delimiter=dialect.delimiter)
    except ValueError:
        # Если ошибка - значит это заголовок (например "Date;Desc..."), пропускаем его
        has_header = True
        print("Header detected, skipping first row")

    for row_idx, row in enumerate(reader):
        if not row or len(row) < 3:
            continue

        try:
            # Ожидаем формат: Дата | Описание | Сумма
            date_raw = row[0]
            desc_raw = row[1]
            amount_raw = row[2]

            # Чистка суммы (1 200,50 -> 1200.50)
            # Удаляем пробелы (разделители тысяч) и меняем запятую на точку
            amount_clean = amount_raw.replace(" ", "").replace(",", ".")
            # Удаляем символы валют если есть
            amount_clean = amount_clean.replace("₽", "").replace("$", "")

            amount = float(amount_clean)
            dt = parse_date(date_raw)

            # Логика определения доход/расход
            # Если сумма > 0, но это трата (магазин), мы должны сохранить её как расход.
            # В CSV обычно всё положительные числа.
            # Пока считаем всё расходом, если нет слова "Зарплата" или "income"
            # В будущем это лучше делать через галочку при импорте.

            is_income = False
            if amount > 0:
                # Простейшая эвристика для вашего примера
                if "зарплата" in desc_raw.lower() or "income" in desc_raw.lower():
                    is_income = True

            print(f"Row {row_idx}: Date={dt.date()}, Desc={desc_raw}, Amount={amount}")

            transactions.append({
                "date": dt,
                "description": desc_raw,
                "amount": abs(amount),
                "is_income": is_income,
                "currency": "RUB"
            })
        except Exception as e:
            print(f"Error parsing row {row}: {e}")
            continue

    print(f"--- PARSING END. Found {len(transactions)} transactions ---")
    return transactions
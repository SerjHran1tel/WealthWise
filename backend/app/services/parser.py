import csv
import io
import re
from datetime import datetime
from typing import List, Dict
from pydantic import ValidationError
from pypdf import PdfReader  # <-- Новая библиотека


def parse_date(date_str: str) -> datetime:
    """Пытается распарсить дату из разных форматов"""
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
    raise ValueError(f"Cannot parse date: {date_str}")


def parse_csv(file_content: bytes) -> List[Dict]:
    """Парсинг CSV файлов (как было раньше)"""
    content_str = file_content.decode("utf-8")
    file_obj = io.StringIO(content_str)

    dialect = csv.Sniffer().sniff(content_str[:1024], delimiters=";,")
    file_obj.seek(0)
    reader = csv.reader(file_obj, delimiter=dialect.delimiter)

    transactions = []

    # Пропуск заголовка (простая эвристика)
    first_row = next(reader, None)
    if not first_row: return []
    try:
        parse_date(first_row[0])
        file_obj.seek(0)
        reader = csv.reader(file_obj, delimiter=dialect.delimiter)
    except ValueError:
        pass  # Это заголовок

    for row in reader:
        if not row or len(row) < 3: continue
        try:
            date_raw = row[0]
            desc_raw = row[1]
            amount_raw = row[2]

            amount_clean = amount_raw.replace(" ", "").replace(",", ".").replace("₽", "")
            amount = float(amount_clean)
            dt = parse_date(date_raw)

            is_income = False
            if amount > 0:
                if "зарплата" in desc_raw.lower() or "income" in desc_raw.lower():
                    is_income = True

            transactions.append({
                "date": dt,
                "description": desc_raw,
                "amount": abs(amount),
                "is_income": is_income,
                "currency": "RUB"
            })
        except Exception as e:
            print(f"CSV Parse Error: {e}")
            continue

    return transactions


def parse_pdf(file_content: bytes) -> List[Dict]:
    """
    Парсинг PDF файлов.
    Извлекает текст и ищет строки, похожие на транзакции.
    """
    transactions = []

    try:
        reader = PdfReader(io.BytesIO(file_content))
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"

        # Разделяем на строки
        lines = full_text.split('\n')

        # Регулярное выражение для поиска транзакций
        # Ищет: Дата (DD.MM.YYYY) + Пробелы + Описание + Пробелы + Сумма (число с точкой или запятой)
        # Пример: 10.12.2025   Пятерочка   1200.50
        # Группы: 1=Дата, 2=Описание, 3=Сумма
        pattern = re.compile(r'(\d{2}\.\d{2}\.\d{4})\s+(.+?)\s+([-+]?\d+[\.,]\d{2})')

        for line in lines:
            line = line.strip()
            match = pattern.search(line)

            if match:
                try:
                    date_str = match.group(1)
                    desc_str = match.group(2).strip()
                    amount_str = match.group(3).replace(',', '.')  # Меняем запятую на точку

                    # Пропускаем строки, если описание похоже на дату (бывает в таблицах)
                    if re.match(r'\d{2}\.\d{2}\.\d{4}', desc_str):
                        continue

                    amount = float(amount_str)
                    dt = parse_date(date_str)

                    # Эвристика: если в PDF сумма с минусом - это расход
                    # Если без минуса - часто в PDF банках расходы пишут просто числом
                    # Тут нужна логика конкретного банка.
                    # Для MVP: считаем всё расходом, если нет слова "пополнение/зарплата"
                    is_income = False
                    if amount > 0 and ("зачисление" in desc_str.lower() or "зарплата" in desc_str.lower()):
                        is_income = True

                    # Если в PDF сумма указана как "-1200", то это точно расход
                    if amount < 0:
                        is_income = False
                        amount = abs(amount)

                    transactions.append({
                        "date": dt,
                        "description": desc_str,
                        "amount": amount,
                        "is_income": is_income,
                        "currency": "RUB"
                    })
                except Exception as e:
                    print(f"PDF Line Error: {line} -> {e}")
                    continue

        print(f"PDF Parsing finished. Found {len(transactions)} items.")
        return transactions

    except Exception as e:
        print(f"Critical PDF Error: {e}")
        return []
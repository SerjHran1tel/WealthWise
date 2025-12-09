import csv
import io
from datetime import datetime
from typing import List, Dict


# TODO: Добавить библиотеку PyPDF2 для PDF
# TODO: Добавить сложную эвристику для определения банка

def parse_date(date_str: str) -> datetime:
    """Пытается распарсить дату из разных форматов"""
    formats = ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%d.%m.%y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return datetime.now()  # Fallback


def parse_csv(file_content: bytes) -> List[Dict]:
    """
    Парсит Generic CSV.
    Ожидаемые заголовки (примерно): Date, Description, Amount
    """
    content_str = file_content.decode("utf-8")
    file_obj = io.StringIO(content_str)
    reader = csv.reader(file_obj, delimiter=';')  # Пробуем ; (Сбер) или ,

    # Эвристика определения разделителя
    first_line = content_str.split('\n')[0]
    if ',' in first_line and ';' not in first_line:
        file_obj.seek(0)
        reader = csv.reader(file_obj, delimiter=',')

    transactions = []

    # Пропускаем заголовки (простая логика, можно улучшить)
    # TODO: Нормальное определение заголовков
    headers = next(reader, None)

    for row in reader:
        if not row or len(row) < 3:
            continue

        try:
            # Хардкод индексов под формат "Дата;Описание;Сумма" (Сбербанк упрощенный)
            # В реальности нужно мапить по headers
            date_raw = row[0]
            desc_raw = row[1] if len(row) > 1 else "No description"
            amount_raw = row[2] if len(row) > 2 else "0"

            # Чистка суммы (1 200,00 -> 1200.00)
            amount_clean = amount_raw.replace(" ", "").replace(",", ".")
            amount = float(amount_clean)

            # Определение доход/расход
            is_income = amount > 0
            # Многие банки пишут расходы с минусом, некоторые нет.
            # Допустим, если файл банка, то расходы часто с минусом.
            # Здесь упростим: считаем модуль суммы расходом, если не указано иное

            transactions.append({
                "date": parse_date(date_raw),
                "description": desc_raw,
                "amount": abs(amount),  # Храним абсолютное значение
                "is_income": amount > 0,  # Временно считаем плюсовые доходом (зависит от банка)
                "currency": "RUB"
            })
        except Exception as e:
            print(f"Error parsing row {row}: {e}")
            continue

    return transactions
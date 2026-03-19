import csv
import io
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from decimal import Decimal, InvalidOperation
from pypdf import PdfReader
from backend.app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ParserError(Exception):
    """Базовая ошибка парсера"""
    pass


class DateParseError(ParserError):
    """Ошибка парсинга даты"""
    pass


class AmountParseError(ParserError):
    """Ошибка парсинга суммы"""
    pass


def parse_date(date_str: str) -> datetime:
    """
    Пытается распарсить дату из разных форматов.
    Возвращает datetime в UTC для единообразия.
    """
    date_str = date_str.strip()

    # Форматы дат в порядке приоритета
    formats = [
        "%d.%m.%Y",  # 10.12.2025
        "%d.%m.%y",  # 10.12.25
        "%Y-%m-%d",  # 2025-12-10
        "%d/%m/%Y",  # 10/12/2025
        "%d-%m-%Y",  # 10-12-2025
        "%Y.%m.%d",  # 2025.12.10
        "%d.%m.%Y %H:%M",  # 10.12.2025 14:30
        "%Y-%m-%d %H:%M:%S",  # 2025-12-10 14:30:00
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Если нет времени, устанавливаем начало дня
            if dt.hour == 0 and dt.minute == 0 and dt.second == 0 and ":" not in date_str:
                dt = dt.replace(hour=0, minute=0, second=0)
            return dt
        except ValueError:
            continue

    raise DateParseError(f"Cannot parse date: {date_str}")


def parse_amount(amount_str: str) -> Decimal:
    """
    Парсит сумму денег из строки, обрабатывая различные форматы.
    Возвращает Decimal для точности.
    """
    if not amount_str or not isinstance(amount_str, str):
        raise AmountParseError(f"Invalid amount string: {amount_str}")

    # Убираем все кроме цифр, точки, запятой и минуса
    amount_clean = re.sub(r'[^\d.,\-+]', '', amount_str.strip())

    # Заменяем запятую на точку (европейский формат)
    amount_clean = amount_clean.replace(',', '.')

    # Убираем лишние точки (оставляем только последнюю для десятичной части)
    parts = amount_clean.split('.')
    if len(parts) > 2:
        # Если несколько точек, последняя - десятичный разделитель
        amount_clean = ''.join(parts[:-1]) + '.' + parts[-1]

    try:
        amount = Decimal(amount_clean)

        # Валидация диапазона
        if abs(amount) < Decimal(str(settings.MIN_AMOUNT)):
            raise AmountParseError(f"Amount too small: {amount}")
        if abs(amount) > Decimal(str(settings.MAX_AMOUNT)):
            raise AmountParseError(f"Amount too large: {amount}")

        return amount
    except (InvalidOperation, ValueError) as e:
        raise AmountParseError(f"Cannot parse amount '{amount_str}': {e}")


def parse_is_income_flag(value: str) -> Optional[bool]:
    """
    Парсит булевый флаг is_income из строки CSV.
    Возвращает True/False или None если не распознано.
    """
    v = value.strip().lower()
    if v in ('true', '1', 'yes', 'да', 'доход', 'income'):
        return True
    if v in ('false', '0', 'no', 'нет', 'расход', 'expense'):
        return False
    return None


def detect_is_income(description: str, amount: Decimal) -> bool:
    """
    Эвристическое определение типа транзакции по описанию и знаку суммы.
    Используется только как fallback, когда в файле нет явного поля is_income.
    """
    # Отрицательная сумма — однозначно расход
    if amount < 0:
        return False

    desc_lower = description.lower()

    # Явные ключевые слова доходов
    income_keywords = [
        'зарплата', 'salary', 'зачисление', 'возврат',
        'income', 'refund', 'cashback', 'аванс', 'премия',
        'bonus', 'дивиденды', 'проценты', 'interest', 'перевод от'
    ]
    for keyword in income_keywords:
        if keyword in desc_lower:
            return True

    # Явные ключевые слова расходов
    expense_keywords = [
        'оплата', 'покупка', 'списание', 'payment', 'purchase',
        'такси', 'продукты', 'кафе', 'ресторан', 'аптека',
        'магазин', 'подписка', 'билет', 'транспорт', 'бензин',
        'коммунальн', 'интернет', 'доставка', 'маникюр', 'стрижка',
        'парикмахер', 'химчистка', 'автомойка'
    ]
    for keyword in expense_keywords:
        if keyword in desc_lower:
            return False

    # Положительная сумма без явных признаков → доход
    return amount > 0


def parse_csv(file_content: bytes) -> Tuple[List[Dict], List[str]]:
    """
    Парсинг CSV файлов.
    Возвращает (список транзакций, список ошибок)
    """
    transactions = []
    errors = []

    try:
        # Определяем кодировку (пробуем UTF-8, затем Windows-1251)
        try:
            content_str = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content_str = file_content.decode('windows-1251')
            except UnicodeDecodeError:
                content_str = file_content.decode('utf-8', errors='ignore')
                errors.append("Warning: File encoding issues detected, some characters may be corrupted")

        file_obj = io.StringIO(content_str)

        # Определяем разделитель
        try:
            dialect = csv.Sniffer().sniff(content_str[:2048], delimiters=";,\t")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ';'  # По умолчанию для русских банков
            errors.append(f"Could not detect delimiter, using '{delimiter}'")

        file_obj.seek(0)
        reader = csv.reader(file_obj, delimiter=delimiter)

        # Пропуск заголовка
        first_row = next(reader, None)
        if not first_row:
            errors.append("Empty file")
            return [], errors

        # Проверяем, является ли первая строка заголовком
        try:
            parse_date(first_row[0])
            # Если парсится как дата, это не заголовок
            file_obj.seek(0)
            reader = csv.reader(file_obj, delimiter=delimiter)
        except (DateParseError, IndexError):
            # Это заголовок, пропускаем
            pass

        row_num = 1
        for row in reader:
            row_num += 1

            if not row or len(row) < 3:
                errors.append(f"Row {row_num}: Too few columns, skipped")
                continue

            try:
                date_raw = row[0].strip()
                desc_raw = row[1].strip()
                amount_raw = row[2].strip()

                if not date_raw or not desc_raw or not amount_raw:
                    errors.append(f"Row {row_num}: Empty required field, skipped")
                    continue

                dt = parse_date(date_raw)
                amount = parse_amount(amount_raw)

                # Читаем is_income явно из CSV (колонка 3), иначе — эвристика
                is_income_raw = row[3].strip() if len(row) > 3 else None
                if is_income_raw is not None:
                    parsed_flag = parse_is_income_flag(is_income_raw)
                    is_income = parsed_flag if parsed_flag is not None else detect_is_income(desc_raw, amount)
                else:
                    is_income = detect_is_income(desc_raw, amount)

                # Читаем валюту из CSV (колонка 4), иначе — дефолт
                currency = row[4].strip() if len(row) > 4 and row[4].strip() else settings.DEFAULT_CURRENCY

                transactions.append({
                    "date": dt,
                    "description": desc_raw[:500],
                    "amount": abs(amount),
                    "is_income": is_income,
                    "currency": currency
                })

            except (DateParseError, AmountParseError) as e:
                errors.append(f"Row {row_num}: {str(e)}")
                continue
            except Exception as e:
                errors.append(f"Row {row_num}: Unexpected error - {str(e)}")
                logger.error(f"CSV parse error at row {row_num}: {e}", exc_info=True)
                continue

            # Защита от слишком больших файлов
            if len(transactions) >= settings.MAX_TRANSACTIONS_PER_FILE:
                errors.append(f"Reached max transactions limit ({settings.MAX_TRANSACTIONS_PER_FILE})")
                break

        logger.info(f"CSV parsing finished. Found {len(transactions)} transactions, {len(errors)} errors")
        return transactions, errors

    except Exception as e:
        logger.error(f"Critical CSV parsing error: {e}", exc_info=True)
        errors.append(f"Critical error: {str(e)}")
        return transactions, errors


def parse_pdf(file_content: bytes) -> Tuple[List[Dict], List[str]]:
    """
    Парсинг PDF файлов банковских выписок.
    Возвращает (список транзакций, список ошибок)
    """
    transactions = []
    errors = []

    try:
        reader = PdfReader(io.BytesIO(file_content))

        if len(reader.pages) == 0:
            errors.append("PDF has no pages")
            return [], errors

        full_text = ""
        for page_num, page in enumerate(reader.pages, 1):
            try:
                full_text += page.extract_text() + "\n"
            except Exception as e:
                errors.append(f"Page {page_num}: Could not extract text - {str(e)}")
                continue

        if not full_text.strip():
            errors.append("No text could be extracted from PDF")
            return [], errors

        lines = full_text.split('\n')

        # Несколько паттернов для разных форматов банков
        patterns = [
            # Паттерн 1: Дата Описание Сумма
            re.compile(r'(\d{2}\.\d{2}\.\d{4})\s+(.+?)\s+([-+]?\d+[\s,.]?\d*[.,]\d{2})'),
            # Паттерн 2: Дата Описание ... Сумма (с возможными промежуточными данными)
            re.compile(r'(\d{2}\.\d{2}\.\d{4})\s+(.+?)\s+(?:.*?)\s+([-+]?\d+[\s,.]?\d*[.,]\d{2})\s*$'),
            # Паттерн 3: Дата и время
            re.compile(r'(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2})\s+(.+?)\s+([-+]?\d+[\s,.]?\d*[.,]\d{2})'),
        ]

        line_num = 0
        for line in lines:
            line_num += 1
            line = line.strip()

            if not line or len(line) < 10:
                continue

            matched = False
            for pattern in patterns:
                match = pattern.search(line)

                if match:
                    try:
                        date_str = match.group(1)
                        desc_str = match.group(2).strip()
                        amount_str = match.group(3)

                        # Пропускаем строки с подозрительным содержимым
                        if re.match(r'\d{2}\.\d{2}\.\d{4}', desc_str):
                            # Описание похоже на дату - это таблица
                            continue

                        if len(desc_str) < 3:
                            # Слишком короткое описание
                            continue

                        dt = parse_date(date_str)
                        amount = parse_amount(amount_str)
                        # PDF не имеет явного поля is_income — используем эвристику с оригинальным знаком
                        is_income = detect_is_income(desc_str, amount)

                        transactions.append({
                            "date": dt,
                            "description": desc_str[:500],
                            "amount": abs(amount),
                            "is_income": is_income,
                            "currency": settings.DEFAULT_CURRENCY
                        })

                        matched = True
                        break

                    except (DateParseError, AmountParseError) as e:
                        errors.append(f"Line {line_num}: {str(e)}")
                        matched = True
                        break
                    except Exception as e:
                        errors.append(f"Line {line_num}: Unexpected error - {str(e)}")
                        logger.error(f"PDF line parse error: {e}", exc_info=True)
                        matched = True
                        break

            # Защита от слишком больших файлов
            if len(transactions) >= settings.MAX_TRANSACTIONS_PER_FILE:
                errors.append(f"Reached max transactions limit ({settings.MAX_TRANSACTIONS_PER_FILE})")
                break

        if not transactions and len(errors) == 0:
            errors.append("No transactions found. PDF format may not be supported.")

        logger.info(f"PDF parsing finished. Found {len(transactions)} transactions, {len(errors)} errors")
        return transactions, errors

    except Exception as e:
        logger.error(f"Critical PDF parsing error: {e}", exc_info=True)
        errors.append(f"Critical error: {str(e)}")
        return transactions, errors
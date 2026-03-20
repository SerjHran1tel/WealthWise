from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, datetime, time
from decimal import Decimal

from backend.app.database import get_db
from backend.app.models import Transaction, Category
from backend.app.schemas import (
    TransactionResponse, UploadResponse, TransactionUpdate,
    PaginationParams
)
from backend.app.services.parser import parse_csv, parse_pdf
from backend.app.agents.classifier import classifier
from backend.app.agents.rag_classifier import rag_classifier
from backend.app.core.config import settings
from backend.app.core.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.post("/upload", response_model=UploadResponse)
async def upload_transactions(
        file: UploadFile = File(...),
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Загрузка транзакций из CSV или PDF файла.
    Поддерживаемые форматы: .csv, .pdf
    """
    filename = file.filename.lower() if file.filename else ""

    if not (filename.endswith('.csv') or filename.endswith('.pdf')):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Only CSV and PDF files are accepted."
        )

    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)

    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    logger.info(f"Processing file: {filename}, size: {file_size_mb:.2f}MB")

    raw_transactions = []
    errors = []

    try:
        if filename.endswith('.csv'):
            raw_transactions, errors = parse_csv(contents)
        elif filename.endswith('.pdf'):
            raw_transactions, errors = parse_pdf(contents)
    except Exception as e:
        logger.error(f"Parser error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

    if not raw_transactions:
        return UploadResponse(
            status="error" if not errors else "warning",
            imported_count=0,
            message="Could not parse any transactions from the file.",
            errors=errors[:10]
        )

    imported_count = 0
    import_errors = []

    for item in raw_transactions:
        try:
            # RAG-классификация: LLM + история + семантический поиск
            try:
                cat_id = await rag_classifier.categorize_with_rag(
                    db, user_id, item['description'], item['amount'],
                    is_income=item.get('is_income', False)
                )
            except Exception as rag_err:
                logger.warning(f"RAG classifier failed, falling back to rule-based: {rag_err}")
                cat_id = classifier.categorize(db, item['description'], item['amount'])

            db_txn = Transaction(
                user_id=user_id,
                date=item['date'],
                description=item['description'],
                amount=item['amount'],
                is_income=item['is_income'],
                currency=item['currency'],
                category_id=cat_id,
                source_file=file.filename
            )

            db.add(db_txn)
            imported_count += 1

        except Exception as e:
            import_errors.append(f"Transaction '{item.get('description', 'unknown')}': {str(e)}")
            logger.error(f"Error importing transaction: {e}", exc_info=True)
            continue

    try:
        db.commit()
        logger.info(f"Successfully imported {imported_count} transactions")
    except Exception as e:
        db.rollback()
        logger.error(f"Database commit error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error saving transactions: {str(e)}"
        )

    all_errors = errors + import_errors

    return UploadResponse(
        status="success" if imported_count > 0 else "error",
        imported_count=imported_count,
        message=f"Successfully imported {imported_count} transactions." +
                (f" {len(all_errors)} errors occurred." if all_errors else ""),
        errors=all_errors[:20] if all_errors else None
    )


@router.get("/", response_model=dict)
async def get_transactions(
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(
            settings.DEFAULT_PAGE_SIZE,
            ge=1,
            le=settings.MAX_PAGE_SIZE,
            description="Размер страницы"
        ),
        start_date: Optional[date] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
        end_date: Optional[date] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
        category_id: Optional[str] = Query(None, description="Фильтр по категории"),
        is_income: Optional[bool] = Query(None, description="Фильтр по типу (доход/расход)"),
        search: Optional[str] = Query(None, description="Поиск по описанию"),
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить список транзакций с пагинацией и фильтрами."""
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    if start_date:
        start_dt = datetime.combine(start_date, time.min)
        query = query.filter(Transaction.date >= start_dt)

    if end_date:
        end_dt = datetime.combine(end_date, time.max)
        query = query.filter(Transaction.date <= end_dt)

    if category_id:
        query = query.filter(Transaction.category_id == category_id)

    if is_income is not None:
        query = query.filter(Transaction.is_income == is_income)

    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))

    total = query.count()

    pagination = PaginationParams(page=page, page_size=page_size)
    transactions = query.order_by(Transaction.date.desc()) \
        .offset(pagination.skip) \
        .limit(pagination.limit) \
        .all()

    return {
        "items": [TransactionResponse.model_validate(t) for t in transactions],
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total_pages": (total + pagination.page_size - 1) // pagination.page_size
    }


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
        transaction_id: str,
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить конкретную транзакцию по ID"""
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return TransactionResponse.model_validate(txn)


@router.delete("/all/clear")
async def clear_all_transactions(
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Удалить ВСЕ транзакции пользователя.
    Используется для сброса данных перед повторным импортом.
    """
    try:
        deleted = db.query(Transaction).filter(Transaction.user_id == user_id).delete()
        db.commit()

        # Сбрасываем кэш RAG классификатора
        rag_classifier.clear_cache()

        logger.info(f"Cleared {deleted} transactions for user {user_id}")
        return {
            "status": "success",
            "deleted_count": deleted,
            "message": f"Удалено {deleted} транзакций. Теперь загрузите файл заново."
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing transactions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error clearing transactions: {str(e)}")


@router.delete("/{transaction_id}")
async def delete_transaction(
        transaction_id: str,
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Удалить транзакцию"""
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    try:
        db.delete(txn)
        db.commit()
        logger.info(f"Transaction {transaction_id} deleted")
        return {"status": "success", "message": "Transaction deleted"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting transaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error deleting transaction")


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
        transaction_id: str,
        update_data: TransactionUpdate,
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Обновить данные транзакции"""
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    try:
        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(txn, field, value)

        txn.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(txn)

        logger.info(f"Transaction {transaction_id} updated")
        return TransactionResponse.model_validate(txn)

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating transaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error updating transaction")


@router.get("/stats/summary")
async def get_transactions_summary(
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить сводную статистику по транзакциям."""
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    if start_date:
        start_dt = datetime.combine(start_date, time.min)
        query = query.filter(Transaction.date >= start_dt)

    if end_date:
        end_dt = datetime.combine(end_date, time.max)
        query = query.filter(Transaction.date <= end_dt)

    income = query.filter(Transaction.is_income == True) \
                 .with_entities(func.sum(Transaction.amount)) \
                 .scalar() or Decimal('0.00')

    expenses = query.filter(Transaction.is_income == False) \
                   .with_entities(func.sum(Transaction.amount)) \
                   .scalar() or Decimal('0.00')

    balance = income - expenses
    total_count = query.count()

    return {
        "total_income": float(income),
        "total_expenses": float(expenses),
        "balance": float(balance),
        "transactions_count": total_count,
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        }
    }
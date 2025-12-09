from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, datetime, time
import uuid

from app.database import get_db
from app.models import Transaction, Category
from app.schemas import TransactionResponse, UploadResponse, TransactionUpdate
from app.services.parser import parse_csv, parse_pdf  # <-- Импортируем parse_pdf
from app.agents.classifier import classifier

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


@router.post("/upload", response_model=UploadResponse)
async def upload_transactions(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    # Проверка расширения
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.pdf')):
        raise HTTPException(status_code=400, detail="Only CSV and PDF supported")

    contents = await file.read()

    # Выбор парсера
    if filename.endswith('.csv'):
        raw_transactions = parse_csv(contents)
    elif filename.endswith('.pdf'):
        raw_transactions = parse_pdf(contents)  # <-- Вызов нового парсера
    else:
        raw_transactions = []

    if not raw_transactions:
        return {
            "status": "warning",
            "imported_count": 0,
            "message": "Could not parse any transactions. Check file format."
        }

    count = 0
    for item in raw_transactions:
        cat_id = classifier.categorize(db, item['description'], item['amount'])

        db_txn = Transaction(
            user_id=TEST_USER_ID,
            date=item['date'],
            description=item['description'],
            amount=item['amount'],
            is_income=item['is_income'],
            currency=item['currency'],
            category_id=cat_id,
            source_file=file.filename
        )
        db.add(db_txn)
        count += 1

    db.commit()
    return {"status": "success", "imported_count": count, "message": "File processed successfully"}


# ... (Остальные методы get, delete, update остаются без изменений)
@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
        skip: int = 0,
        limit: int = 1000,
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(Transaction.user_id == TEST_USER_ID)

    if start_date:
        start_dt = datetime.combine(start_date, time.min)
        query = query.filter(Transaction.date >= start_dt)

    if end_date:
        end_dt = datetime.combine(end_date, time.max)
        query = query.filter(Transaction.date <= end_dt)

    return query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()


@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: str, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(txn)
    db.commit()
    return {"status": "success", "message": "Deleted"}


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
        transaction_id: str,
        update_data: TransactionUpdate,
        db: Session = Depends(get_db)
):
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if update_data.category_id is not None:
        txn.category_id = update_data.category_id
    if update_data.description is not None:
        txn.description = update_data.description
    if update_data.is_income is not None:
        txn.is_income = update_data.is_income

    db.commit()
    db.refresh(txn)
    return txn
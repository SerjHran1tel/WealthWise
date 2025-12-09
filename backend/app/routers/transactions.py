from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import uuid

from app.database import get_db
from app.models import Transaction, Category
from app.schemas import TransactionResponse, UploadResponse, TransactionUpdate
from app.services.parser import parse_csv
from app.agents.classifier import classifier

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


@router.post("/upload", response_model=UploadResponse)
async def upload_transactions(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV supported in MVP")

    contents = await file.read()

    # 1. Парсинг
    raw_transactions = parse_csv(contents)

    count = 0
    for item in raw_transactions:
        # 2. Классификация
        cat_id = classifier.categorize(db, item['description'], item['amount'])

        # 3. Сохранение
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

    return {
        "status": "success",
        "imported_count": count,
        "message": "File processed successfully"
    }


@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
        skip: int = 0,
        limit: int = 1000,
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(Transaction.user_id == TEST_USER_ID)

    # Применяем фильтры по дате, если они переданы
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

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

    # Обновляем поля, если они переданы
    if update_data.category_id is not None:
        txn.category_id = update_data.category_id
    if update_data.description is not None:
        txn.description = update_data.description
    if update_data.is_income is not None:
        txn.is_income = update_data.is_income

    db.commit()
    db.refresh(txn)
    return txn
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.financial_record import FinancialRecord
from app.schemas.financial_record import RecordCreate, RecordUpdate, RecordFilters


def _base_query(db: Session):
    """All queries exclude soft-deleted records."""
    return db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)


def get_record_by_id(db: Session, record_id: int) -> FinancialRecord:
    record = _base_query(db).filter(FinancialRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record


def list_records(db: Session, filters: RecordFilters) -> tuple[int, list[FinancialRecord]]:
    query = _base_query(db)

    if filters.type:
        query = query.filter(FinancialRecord.type == filters.type)
    if filters.category:
        query = query.filter(FinancialRecord.category == filters.category.strip().lower())
    if filters.date_from:
        query = query.filter(FinancialRecord.record_date >= filters.date_from)
    if filters.date_to:
        query = query.filter(FinancialRecord.record_date <= filters.date_to)

    total = query.count()
    offset = (filters.page - 1) * filters.page_size
    records = (
        query.order_by(FinancialRecord.record_date.desc(), FinancialRecord.id.desc())
        .offset(offset)
        .limit(filters.page_size)
        .all()
    )
    return total, records


def create_record(db: Session, payload: RecordCreate, created_by: int) -> FinancialRecord:
    record = FinancialRecord(
        amount=payload.amount,
        type=payload.type,
        category=payload.category,
        record_date=payload.record_date,
        description=payload.description,
        created_by=created_by,
        is_deleted=False,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_record(db: Session, record_id: int, payload: RecordUpdate) -> FinancialRecord:
    record = get_record_by_id(db, record_id)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    for field, value in update_data.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


def delete_record(db: Session, record_id: int) -> None:
    """Soft delete: mark is_deleted = True instead of removing the row."""
    record = get_record_by_id(db, record_id)
    record.is_deleted = True
    db.commit()

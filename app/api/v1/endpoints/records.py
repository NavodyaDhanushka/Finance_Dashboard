from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import require_permission, get_current_user
from app.models.user import User
from app.schemas.financial_record import (
    RecordCreate,
    RecordUpdate,
    RecordResponse,
    RecordListResponse,
    RecordFilters,
    RecordType,
)
from app.services import record_service

router = APIRouter(prefix="/records", tags=["Financial Records"])


@router.get(
    "",
    response_model=RecordListResponse,
    summary="List records with optional filtering [Viewer+]",
    dependencies=[Depends(require_permission("records:read"))],
)
def list_records(
    type: Optional[RecordType] = Query(None, description="Filter by income or expense"),
    category: Optional[str] = Query(None, description="Filter by category name"),
    date_from: Optional[date] = Query(None, description="Earliest record date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Latest record date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    filters = RecordFilters(
        type=type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    total, records = record_service.list_records(db, filters)
    return RecordListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=records,
    )


@router.post(
    "",
    response_model=RecordResponse,
    status_code=201,
    summary="Create a financial record [Admin only]",
)
def create_record(
    payload: RecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("records:create")),
):
    return record_service.create_record(db, payload, created_by=current_user.id)


@router.get(
    "/{record_id}",
    response_model=RecordResponse,
    summary="Get a single record [Viewer+]",
    dependencies=[Depends(require_permission("records:read"))],
)
def get_record(record_id: int, db: Session = Depends(get_db)):
    return record_service.get_record_by_id(db, record_id)


@router.patch(
    "/{record_id}",
    response_model=RecordResponse,
    summary="Update a record [Admin only]",
    dependencies=[Depends(require_permission("records:update"))],
)
def update_record(record_id: int, payload: RecordUpdate, db: Session = Depends(get_db)):
    return record_service.update_record(db, record_id, payload)


@router.delete(
    "/{record_id}",
    status_code=204,
    summary="Soft-delete a record [Admin only]",
    dependencies=[Depends(require_permission("records:delete"))],
)
def delete_record(record_id: int, db: Session = Depends(get_db)):
    record_service.delete_record(db, record_id)

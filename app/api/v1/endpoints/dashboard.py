from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import require_permission
from app.schemas.dashboard import DashboardSummary
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Get dashboard summary with aggregated financial data [Viewer+]",
    dependencies=[Depends(require_permission("dashboard:read"))],
)
def get_summary(
    date_from: Optional[date] = Query(None, description="Start date for summary range (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date for summary range (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    return dashboard_service.get_dashboard_summary(db, date_from=date_from, date_to=date_to)

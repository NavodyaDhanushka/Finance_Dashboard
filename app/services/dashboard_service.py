from decimal import Decimal
from datetime import date
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.financial_record import FinancialRecord
from app.schemas.dashboard import (
    DashboardSummary,
    CategoryTotal,
    MonthlyTrend,
    RecentActivity,
)


def _active_records(db: Session):
    return db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)


def get_dashboard_summary(
    db: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> DashboardSummary:
    base = _active_records(db)
    if date_from:
        base = base.filter(FinancialRecord.record_date >= date_from)
    if date_to:
        base = base.filter(FinancialRecord.record_date <= date_to)

    # ── Totals ──────────────────────────────────────────────────────────────
    totals = (
        base.with_entities(
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
            func.count(FinancialRecord.id).label("count"),
        )
        .group_by(FinancialRecord.type)
        .all()
    )

    total_income = Decimal("0")
    total_expenses = Decimal("0")
    record_count = 0
    for row in totals:
        if row.type == "income":
            total_income = row.total or Decimal("0")
        elif row.type == "expense":
            total_expenses = row.total or Decimal("0")
        record_count += row.count

    # ── Category breakdowns ──────────────────────────────────────────────────
    cat_query = (
        base.with_entities(
            FinancialRecord.type,
            FinancialRecord.category,
            func.sum(FinancialRecord.amount).label("total"),
            func.count(FinancialRecord.id).label("count"),
        )
        .group_by(FinancialRecord.type, FinancialRecord.category)
        .order_by(func.sum(FinancialRecord.amount).desc())
        .all()
    )

    income_by_category = [
        CategoryTotal(category=r.category, total=r.total or Decimal("0"), count=r.count)
        for r in cat_query
        if r.type == "income"
    ]
    expense_by_category = [
        CategoryTotal(category=r.category, total=r.total or Decimal("0"), count=r.count)
        for r in cat_query
        if r.type == "expense"
    ]

    # ── Monthly trends (last 12 months) ─────────────────────────────────────
    monthly_raw = (
        base.with_entities(
            func.year(FinancialRecord.record_date).label("year"),
            func.month(FinancialRecord.record_date).label("month"),
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
        )
        .group_by(
            func.year(FinancialRecord.record_date),
            func.month(FinancialRecord.record_date),
            FinancialRecord.type,
        )
        .order_by(
            func.year(FinancialRecord.record_date),
            func.month(FinancialRecord.record_date),
        )
        .limit(24)  # up to 12 months × 2 types
        .all()
    )

    # Merge income/expense rows into single MonthlyTrend objects
    monthly_map: dict[tuple, dict] = {}
    for row in monthly_raw:
        key = (row.year, row.month)
        if key not in monthly_map:
            monthly_map[key] = {"income": Decimal("0"), "expenses": Decimal("0")}
        if row.type == "income":
            monthly_map[key]["income"] = row.total or Decimal("0")
        else:
            monthly_map[key]["expenses"] = row.total or Decimal("0")

    monthly_trends = [
        MonthlyTrend(
            year=y,
            month=m,
            income=v["income"],
            expenses=v["expenses"],
            net=v["income"] - v["expenses"],
        )
        for (y, m), v in sorted(monthly_map.items())
    ]

    # ── Recent activity (last 10 records) ───────────────────────────────────
    recent_records = (
        base.order_by(
            FinancialRecord.record_date.desc(),
            FinancialRecord.id.desc(),
        )
        .limit(10)
        .all()
    )
    recent_activity = [
        RecentActivity(
            id=r.id,
            amount=r.amount,
            type=r.type,
            category=r.category,
            record_date=str(r.record_date),
            description=r.description,
        )
        for r in recent_records
    ]

    return DashboardSummary(
        total_income=total_income,
        total_expenses=total_expenses,
        net_balance=total_income - total_expenses,
        record_count=record_count,
        income_by_category=income_by_category,
        expense_by_category=expense_by_category,
        monthly_trends=monthly_trends,
        recent_activity=recent_activity,
    )

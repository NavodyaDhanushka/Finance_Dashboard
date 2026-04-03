from decimal import Decimal
from pydantic import BaseModel


class CategoryTotal(BaseModel):
    category: str
    total: Decimal
    count: int


class MonthlyTrend(BaseModel):
    year: int
    month: int
    income: Decimal
    expenses: Decimal
    net: Decimal


class RecentActivity(BaseModel):
    id: int
    amount: Decimal
    type: str
    category: str
    record_date: str
    description: str | None


class DashboardSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    record_count: int
    income_by_category: list[CategoryTotal]
    expense_by_category: list[CategoryTotal]
    monthly_trends: list[MonthlyTrend]
    recent_activity: list[RecentActivity]

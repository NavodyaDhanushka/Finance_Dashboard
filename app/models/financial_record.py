from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, Date, DateTime, Enum as SAEnum, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RecordType(str):
    INCOME = "income"
    EXPENSE = "expense"


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    type: Mapped[str] = mapped_column(
        SAEnum("income", "expense", name="record_type_enum"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Audit fields
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_records_type_date", "type", "record_date"),
        Index("ix_records_category_date", "category", "record_date"),
    )

    def __repr__(self) -> str:
        return f"<FinancialRecord id={self.id} type={self.type} amount={self.amount}>"

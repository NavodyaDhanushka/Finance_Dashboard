from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


RecordType = Literal["income", "expense"]


class RecordCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Must be positive")
    type: RecordType
    category: str = Field(..., min_length=1, max_length=100)
    record_date: date
    description: Optional[str] = Field(None, max_length=2000)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v: str) -> str:
        return v.strip().lower()


class RecordUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    type: Optional[RecordType] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    record_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=2000)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v: str | None) -> str | None:
        return v.strip().lower() if v else v


class RecordResponse(BaseModel):
    id: int
    amount: Decimal
    type: str
    category: str
    record_date: date
    description: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecordListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RecordResponse]


class RecordFilters(BaseModel):
    type: Optional[RecordType] = None
    category: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

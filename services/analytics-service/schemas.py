from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, List


class BudgetCreate(BaseModel):
    """Schema for creating a budget"""
    category_id: Optional[int] = None
    amount: float = Field(..., gt=0)
    period: str = Field(..., pattern="^(monthly|yearly)$")
    start_date: datetime
    end_date: datetime


class BudgetResponse(BaseModel):
    """Schema for budget response"""
    id: int
    user_id: int
    category_id: Optional[int]
    amount: float
    period: str
    start_date: datetime
    end_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class SpendingSummary(BaseModel):
    """Schema for spending summary"""
    total_expenses: float
    expense_count: int
    average_expense: float
    period_start: datetime
    period_end: datetime


class CategoryBreakdown(BaseModel):
    """Schema for category-wise breakdown"""
    category_id: int
    category_name: str
    total_amount: float
    expense_count: int
    percentage: float


class BudgetStatus(BaseModel):
    """Schema for budget status"""
    budget_id: int
    budget_amount: float
    spent_amount: float
    remaining_amount: float
    percentage_used: float
    is_exceeded: bool
    category_id: Optional[int]
    period: str


class TrendData(BaseModel):
    """Schema for trend data"""
    date: str
    amount: float


class SpendingTrends(BaseModel):
    """Schema for spending trends"""
    period: str
    data: List[TrendData]

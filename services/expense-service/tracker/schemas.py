from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    """Schema for creating a category"""
    pass


class CategoryResponse(CategoryBase):
    """Schema for category response"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CategoryCreateResponse(BaseModel):
    success: bool 
    message: str 
    data: CategoryResponse


class ExpenseBase(BaseModel):
    """Base expense schema"""
    amount: float = Field(..., gt=0, description="Amount must be greater than 0")
    category_id: int
    description: Optional[str] = None
    date: Optional[datetime] = None


class ExpenseCreate(ExpenseBase):
    """Schema for creating an expense"""
    pass


class ExpenseUpdate(BaseModel):
    """Schema for updating an expense"""
    amount: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = None
    description: Optional[str] = None
    date: Optional[datetime] = None


class ExpenseResponse(ExpenseBase):
    """Schema for expense response"""
    id: int
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
    


class ExpenseWithCategory(ExpenseResponse):
    """Schema for expense with category details"""
    category_name: str

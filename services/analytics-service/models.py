from sqlalchemy import Column, Integer, Float, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Budget(Base):
    """Budget model"""
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    category_id = Column(Integer, nullable=True)  # None means overall budget
    amount = Column(Float, nullable=False)
    period = Column(String(20), nullable=False)  # 'monthly', 'yearly'
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Budget {self.id}: ${self.amount} {self.period}>"


class ExpenseCache(Base):
    """Cache for expense data from Expense Service"""
    __tablename__ = "expense_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, unique=True, nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ExpenseCache {self.expense_id}: ${self.amount}>"

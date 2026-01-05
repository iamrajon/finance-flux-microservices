from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta
import pandas as pd
import httpx
import os

from database import get_db, engine
from models import Base, Budget, ExpenseCache
from schemas import (
    BudgetCreate, BudgetResponse, SpendingSummary,
    CategoryBreakdown, BudgetStatus, SpendingTrends, TrendData
)
from consumer import init_consumer

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Analytics Service",
    description="Microservice for expense analytics and insights",
    version="1.0.0"
)

# Start RabbitMQ consumer
@app.on_event("startup")
async def startup_event():
    """Initialize consumer on startup"""
    init_consumer()


def get_user_id(x_user_id: str = Header(...)) -> int:
    """Extract user ID from header"""
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"service": "Analytics Service", "status": "healthy"}


# ==================== BUDGET ENDPOINTS ====================

@app.post("/api/analytics/budget", response_model=BudgetResponse, status_code=201)
async def create_budget(
    budget: BudgetCreate,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Create a new budget"""
    db_budget = Budget(**budget.dict(), user_id=user_id)
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    
    return db_budget


@app.get("/api/analytics/budget", response_model=List[BudgetResponse])
async def list_budgets(
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """List all budgets for user"""
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
    return budgets


@app.get("/api/analytics/budget-status", response_model=List[BudgetStatus])
async def get_budget_status(
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Get budget status with spending comparison"""
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
    
    result = []
    for budget in budgets:
        # Calculate spent amount from cache
        query = db.query(func.sum(ExpenseCache.amount)).filter(
            ExpenseCache.user_id == user_id,
            ExpenseCache.date >= budget.start_date,
            ExpenseCache.date <= budget.end_date
        )
        
        if budget.category_id:
            query = query.filter(ExpenseCache.category_id == budget.category_id)
        
        spent = query.scalar() or 0.0
        remaining = budget.amount - spent
        percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0
        
        result.append(BudgetStatus(
            budget_id=budget.id,
            budget_amount=budget.amount,
            spent_amount=spent,
            remaining_amount=remaining,
            percentage_used=round(percentage, 2),
            is_exceeded=spent > budget.amount,
            category_id=budget.category_id,
            period=budget.period
        ))
    
    return result


# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/api/analytics/summary", response_model=SpendingSummary)
async def get_spending_summary(
    user_id: int = Depends(get_user_id),
    start_date: datetime = None,
    end_date: datetime = None,
    db: Session = Depends(get_db)
):
    """Get spending summary for a period"""
    # Default to last 30 days
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Query from cache
    expenses = db.query(ExpenseCache).filter(
        ExpenseCache.user_id == user_id,
        ExpenseCache.date >= start_date,
        ExpenseCache.date <= end_date
    ).all()
    
    total = sum(e.amount for e in expenses)
    count = len(expenses)
    average = total / count if count > 0 else 0
    
    return SpendingSummary(
        total_expenses=round(total, 2),
        expense_count=count,
        average_expense=round(average, 2),
        period_start=start_date,
        period_end=end_date
    )


@app.get("/api/analytics/by-category", response_model=List[CategoryBreakdown])
async def get_category_breakdown(
    user_id: int = Depends(get_user_id),
    start_date: datetime = None,
    end_date: datetime = None,
    db: Session = Depends(get_db)
):
    """Get spending breakdown by category"""
    # Default to last 30 days
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Query from cache
    expenses = db.query(ExpenseCache).filter(
        ExpenseCache.user_id == user_id,
        ExpenseCache.date >= start_date,
        ExpenseCache.date <= end_date
    ).all()
    
    # Group by category
    df = pd.DataFrame([{
        'category_id': e.category_id,
        'amount': e.amount
    } for e in expenses])
    
    if df.empty:
        return []
    
    grouped = df.groupby('category_id').agg({
        'amount': ['sum', 'count']
    }).reset_index()
    
    total_amount = df['amount'].sum()
    
    # Fetch category names from Expense Service
    result = []
    for _, row in grouped.iterrows():
        category_id = int(row['category_id'])
        amount = float(row['amount']['sum'])
        count = int(row['amount']['count'])
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0
        
        # Get category name (simplified - in production, cache this)
        category_name = f"Category {category_id}"
        
        result.append(CategoryBreakdown(
            category_id=category_id,
            category_name=category_name,
            total_amount=round(amount, 2),
            expense_count=count,
            percentage=round(percentage, 2)
        ))
    
    return sorted(result, key=lambda x: x.total_amount, reverse=True)


@app.get("/api/analytics/trends", response_model=SpendingTrends)
async def get_spending_trends(
    user_id: int = Depends(get_user_id),
    period: str = "monthly",  # 'daily', 'weekly', 'monthly'
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get spending trends over time"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Query from cache
    expenses = db.query(ExpenseCache).filter(
        ExpenseCache.user_id == user_id,
        ExpenseCache.date >= start_date,
        ExpenseCache.date <= end_date
    ).all()
    
    if not expenses:
        return SpendingTrends(period=period, data=[])
    
    # Create DataFrame
    df = pd.DataFrame([{
        'date': e.date,
        'amount': e.amount
    } for e in expenses])
    
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by period
    if period == 'daily':
        df['period'] = df['date'].dt.date
    elif period == 'weekly':
        df['period'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time.date())
    else:  # monthly
        df['period'] = df['date'].dt.to_period('M').apply(lambda r: r.start_time.date())
    
    grouped = df.groupby('period')['amount'].sum().reset_index()
    
    trend_data = [
        TrendData(date=str(row['period']), amount=round(float(row['amount']), 2))
        for _, row in grouped.iterrows()
    ]
    
    return SpendingTrends(period=period, data=trend_data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

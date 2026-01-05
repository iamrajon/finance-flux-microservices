from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from tracker.database import get_db
from tracker.schemas import (
    CategoryBase,
    CategoryCreate,
    CategoryResponse,
    CategoryCreateResponse,
    ExpenseBase,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    ExpenseWithCategory
)
from tracker.models import Base, Expense, Category
from tracker.events import publish_event
from tracker.dependencies import get_user_id 
from datetime import datetime, timezone


app = FastAPI(
    title="Expense Tracker API", 
    description="Microservice for managing Expenses",
    version="0.0.1"
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"service": "Expense Service", "status": "healthy"}


"""Api Endpoits for Expense Module"""
@app.post(
    "/api/expenses/categories", 
    response_model=CategoryCreateResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db)
):
    """create a new expense category"""
    category_name = category.name
    # check if category_name already exists
    existing = db.query(Category).filter(Category.name == category_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists!")
    
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    response_data = {
        "success": True,
        "message": "Category Created Successfully!",
        "data": db_category
    }

    return response_data

@app.get("/api/expenses/categories", response_model=List[CategoryResponse])
async def list_categories(db: Session = Depends(get_db)):
    """List all exptense categories"""
    categories = db.query(Category).all()
    return categories 

@app.get("/api/expenses/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get a specific category by its id"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found!")
    return category


# expense realted endpoints
@app.post("/api/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense: ExpenseCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Create a new expense"""
    category = db.query(Category).filter(Category.id == expense.category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="category not found!")
    
    expense_data = expense.model_dump()
    if expense_data.get("date") is None:
        expense_data['date'] = datetime.now(timezone.utc)

    db_expense = Expense(**expense_data, user_id=user_id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    # publish evvent to queue
    publish_event('expense.created', {
        'expense_id': db_expense.id,
        'user_id': user_id,
        'amount': db_expense.amount,
        'category_id': db_expense.category_id,
        'date': db_expense.date.isoformat()
    })

    return db_expense


@app.get("/api/expenses", response_model=List[ExpenseWithCategory])
async def list_expenses(
    user_id: str = Depends(get_user_id),
    category_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all expenses with filters"""
    query = db.query(Expense).filter(Expense.user_id == user_id)

    # Apply filters 
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    if min_amount:
        query = query.filter(Expense.amount >= min_amount)
    if max_amount:
        query = query.filter(Expense.amount <= max_amount)
    
    expenses = query.order_by(Expense.date.desc()).offset(skip).limit(limit).all()

    # Add category name to each expense
    result = []
    for expense in expenses:
        category = db.query(Category).filter(Category.id == expense.category_id).first()
        expense_dict = ExpenseResponse.model_validate(expense).model_dump()
        expense_dict['category_name'] = category.name if category else "Unknown"
        result.append(expense_dict)

    return result 

@app.get("/api/expenses/{expense_id}", response_model=ExpenseWithCategory)
async def get_expense(
    expense_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Get a specific expense"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user_id
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    category = db.query(Category).filter(Category.id == expense.category_id).first()
    expense_dict = ExpenseResponse.model_validate(expense).model_dump()
    expense_dict['category_name'] = category.name if category else "Unknown"
    
    return expense_dict


@app.put("/api/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Update an expense"""
    db_expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user_id
    ).first()
    
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Update fields
    # update_data = expense_update.dict(exclude_unset=True)
    update_data = expense_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_expense, field, value)
    
    db.commit()
    db.refresh(db_expense)

    # Publish event
    publish_event('expense.updated', {
        'expense_id': db_expense.id,
        'user_id': user_id,
        'amount': db_expense.amount,
        'category_id': db_expense.category_id
    })
    
    return db_expense


@app.delete("/api/expenses/{expense_id}", status_code=204)
async def delete_expense(
    expense_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Delete an expense"""
    db_expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user_id
    ).first()
    
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(db_expense)
    db.commit()
    
    # Publish event
    publish_event('expense.deleted', {
        'expense_id': expense_id,
        'user_id': user_id
    })
    
    return None


# uvicorn tracker.main:app --reload
# uvicorn tracker.main:app --host 0.0.0.0 --port 8000
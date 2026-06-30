from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Trade

router = APIRouter()

@router.get("/")
def get_journal(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    trades = db.query(Trade).offset(skip).limit(limit).all()
    return trades

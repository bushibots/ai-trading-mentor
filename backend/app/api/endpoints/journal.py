from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
from app.db.database import get_db
from app.db.models import Trade, TradeReview
from app.schemas.request import TradeReviewRequest

router = APIRouter()

@router.get("/")
def get_journal(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    # Order by newest first
    trades = db.query(Trade).order_by(desc(Trade.timestamp)).offset(skip).limit(limit).all()
    return trades

@router.post("/{trade_id}/review")
def review_trade(trade_id: int, review_data: TradeReviewRequest, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
        
    if trade.review:
        raise HTTPException(status_code=400, detail="Trade already reviewed")
        
    # Update trade outcome
    trade.outcome = review_data.result
    
    # Create review
    new_review = TradeReview(
        trade_id=trade_id,
        result=review_data.result,
        why_succeeded=review_data.why_succeeded,
        why_failed=review_data.why_failed,
        lessons_learned=review_data.lessons_learned,
        patterns_worked=json.dumps(review_data.patterns_worked) if review_data.patterns_worked else "[]",
        patterns_failed=json.dumps(review_data.patterns_failed) if review_data.patterns_failed else "[]"
    )
    
    db.add(new_review)
    db.commit()
    db.refresh(trade)
    
    return {"message": "Review saved successfully", "outcome": trade.outcome}

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db.models import Trade

router = APIRouter()

@router.get("/")
def get_stats(db: Session = Depends(get_db)):
    total_trades = db.query(func.count(Trade.id)).scalar()
    # Placeholder for more complex stats
    return {
        "total_trades_analyzed": total_trades,
        "win_rate": "N/A (Requires Outcome Tracking)",
        "most_reliable_timeframe": "15m"
    }

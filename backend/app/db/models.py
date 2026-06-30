from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.database import Base

class SignalEnum(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WAIT = "WAIT"
    CONFLICT = "CONFLICT"

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    asset = Column(String, index=True)
    timeframe = Column(String, index=True)
    screenshot_path = Column(String)
    
    # Analysis Details
    indicators = Column(Text) # JSON string of local indicators
    pattern = Column(String)
    
    # AI Decision
    decision = Column(String) # BUY, SELL, HOLD, WAIT, CONFLICT
    confidence = Column(Float)
    reason = Column(Text)
    educational_concepts = Column(Text) # JSON string
    bull_factors = Column(Text) # JSON string
    bear_factors = Column(Text) # JSON string
    
    # Outcome tracking
    outcome = Column(String, nullable=True) # e.g. "WIN", "LOSS", "BREAK_EVEN"
    
    review = relationship("TradeReview", back_populates="trade", uselist=False)

class TradeReview(Base):
    __tablename__ = "trade_reviews"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"))
    
    result = Column(String)
    why_succeeded = Column(Text)
    why_failed = Column(Text)
    lessons_learned = Column(Text)
    patterns_worked = Column(Text) # JSON string
    patterns_failed = Column(Text) # JSON string
    
    trade = relationship("Trade", back_populates="review")

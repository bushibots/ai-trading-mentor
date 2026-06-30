from pydantic import BaseModel, Field
from typing import Optional, List

class AnalysisRequest(BaseModel):
    asset: str = Field(..., description="The asset pair being analyzed, e.g., BTC/USD")
    timeframe: str = Field(..., description="The timeframe of the chart, e.g., 15m, 1h, 4h, 24h")
    # Base64 string of the image, or handling it via multipart form data in the endpoint.
    # In a real setup, we might receive multipart/form-data for the image and standard fields.
    # So we might not use this schema directly for the image upload endpoint, but useful for internal passing.
    
class TradeReviewRequest(BaseModel):
    trade_id: int
    result: str = Field(..., description="e.g., WIN, LOSS, BREAK_EVEN")
    why_succeeded: Optional[str] = None
    why_failed: Optional[str] = None
    lessons_learned: Optional[str] = None
    patterns_worked: Optional[List[str]] = []
    patterns_failed: Optional[List[str]] = []

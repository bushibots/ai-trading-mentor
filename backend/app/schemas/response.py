from pydantic import BaseModel, Field
from typing import List, Optional

class EducationalConcept(BaseModel):
    concept_name: str
    explanation: str
    real_world_usage: str
    advantages: Optional[str] = None
    disadvantages: Optional[str] = None
    common_mistakes: Optional[str] = None
    risk: Optional[str] = None

class ExtractedDataSchema(BaseModel):
    support_levels: List[float] = Field(default_factory=list, description="Identified support price levels")
    resistance_levels: List[float] = Field(default_factory=list, description="Identified resistance price levels")
    trend_direction: str = Field(..., description="UP, DOWN, or SIDEWAYS")
    observed_patterns: List[str] = Field(default_factory=list, description="Raw chart patterns detected")
    volume_anomalies: Optional[str] = Field(default=None, description="Any spikes or drops in volume observed in the image")
    key_observations: List[str] = Field(default_factory=list, description="Raw structural observations")

class AnalystRecommendationSchema(BaseModel):
    signal: str = Field(..., description="BUY, SELL, HOLD, WAIT, or CONFLICT")
    confidence: float = Field(..., ge=0, le=100)
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    time_horizon: Optional[str] = None
    wait_duration_recommendation: Optional[str] = None
    bull_factors: List[str] = Field(default_factory=list)
    bear_factors: List[str] = Field(default_factory=list)
    invalidation_conditions: List[str] = Field(default_factory=list)
    logic_reasoning: List[str] = Field(default_factory=list, description="The analyst's mathematical or structural reasoning")

class AIAnalysisResponse(BaseModel):
    signal: str = Field(..., description="BUY, SELL, HOLD, WAIT, CONFLICT")
    confidence: float = Field(..., ge=0, le=100, description="Confidence score from 0 to 100")
    reasons: List[str] = Field(..., description="Reasons for the decision")
    bull_factors: List[str] = Field(..., description="Bullish arguments")
    bear_factors: List[str] = Field(..., description="Bearish arguments")
    pattern_names: List[str] = Field(..., description="Identified patterns on the chart")
    concept_names: List[str] = Field(..., description="Concepts utilized in this analysis")
    educational_explanations: List[EducationalConcept] = Field(..., description="Detailed educational breakdown")
    wait_duration_recommendation: Optional[str] = Field(default=None, description="Precise wait duration if signal is WAIT, e.g., '30m' or 'Until 4H close'")
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    time_horizon: Optional[str] = None
    expiration_time: Optional[str] = None
    invalidation_conditions: Optional[List[str]] = None
    additional_comments: Optional[str] = Field(default=None, description="Any extra thoughts or warnings from the mentor")
    current_price: Optional[float] = Field(default=0.0, description="The live current price of the asset")
    annotated_chart_base64: Optional[str] = Field(default=None, description="Base64 encoded string of the annotated chart image")

class ErrorResponse(BaseModel):
    detail: str

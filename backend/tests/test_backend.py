import pytest
import pandas as pd
from app.services.indicators import IndicatorService
from app.services.market_readiness import MarketReadinessService
from app.services.education import EducationService

def test_indicator_calculation():
    # Create mock data
    data = {
        "close": [100.0 + i for i in range(30)] # Upward trend
    }
    df = pd.DataFrame(data)
    
    indicators = IndicatorService.calculate_indicators(df)
    
    assert "ema_9" in indicators
    assert "ema_21" in indicators
    assert "rsi_14" in indicators
    assert indicators["trend"] == "bullish"
    assert isinstance(indicators["rsi_14"], float)

def test_market_readiness_analyze():
    # High volume case
    data_ok = {"volume": 500}
    status_ok = MarketReadinessService.analyze_readiness(data_ok)
    assert status_ok == "ANALYZE"
    
    # Low volume case
    data_wait = {"volume": 50}
    status_wait = MarketReadinessService.analyze_readiness(data_wait)
    assert status_wait == "WAIT"

def test_education_service_enrichment():
    patterns = ["Bullish Engulfing", "Unknown Concept"]
    enriched = EducationService.enrich_with_education(patterns)
    
    assert len(enriched) == 2
    assert enriched[0].concept_name == "Bullish Engulfing"
    assert "reversal" in enriched[0].real_world_usage.lower()
    
    assert enriched[1].concept_name == "Unknown Concept"
    assert "detailed educational breakdown is not currently" in enriched[1].explanation

from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import json
import base64

from app.db.database import get_db
from app.db.models import Trade
from app.schemas.response import AIAnalysisResponse
from app.services.market_readiness import MarketReadinessService
from app.services.market_data import MarketDataService
from app.services.education import EducationService
from app.ai.gemini_provider import GeminiProvider

router = APIRouter()
ai_provider = GeminiProvider()

@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_chart(
    asset: str = Form(...),
    timeframe: str = Form(...),
    user_notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        # 1 & 2. Fetch live market data, plot image, and extract latest indicators
        try:
            df, ind_dict, clean_ticker = MarketDataService.fetch_data(asset, timeframe)
            # Calculate local technical indicators (EMA, RSI, etc.)
            from app.services.indicators import IndicatorService
            tech_indicators = IndicatorService.calculate_indicators(df)
            ind_dict.update(tech_indicators)
            
            tmp_path = MarketDataService.plot_chart(df, clean_ticker, timeframe)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # 3. Fetch previous context for threading
        from sqlalchemy import desc
        last_trade = db.query(Trade).filter(
            Trade.asset == asset,
            Trade.timeframe == timeframe
        ).order_by(desc(Trade.timestamp)).first()
        
        previous_context = None
        if last_trade:
            previous_context = f"Timestamp: {last_trade.timestamp}, Signal: {last_trade.decision}, Confidence: {last_trade.confidence}%, Reasons: {last_trade.reason}"
        
        # 4. Market Readiness Check
        readiness = MarketReadinessService.analyze_readiness(ind_dict)
        if readiness == "WAIT":
            return AIAnalysisResponse(
                signal="WAIT",
                confidence=100,
                reasons=["Market conditions are not suitable for analysis based on local indicator check (e.g., low volume)."],
                bull_factors=[],
                bear_factors=[],
                pattern_names=[],
                concept_names=[],
                educational_explanations=[]
            )
            
        # 5. AI Analysis
        ai_response_str = await ai_provider.analyze_chart(
            image_path=tmp_path,
            timeframe=timeframe,
            indicators=ind_dict,
            previous_context=previous_context,
            user_notes=user_notes
        )
        
        try:
            ai_data = json.loads(ai_response_str)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse AI response as JSON.")
            
        # 5. Enrich with Educational Content
        concepts = ai_data.get("concept_names", [])
        patterns = ai_data.get("pattern_names", [])
        combined_concepts = concepts + patterns
        edu_explanations = EducationService.enrich_with_education(combined_concepts)
        
        # 6. Generate Annotated Projection Chart
        target_price = ai_data.get("target")
        stop_loss_price = ai_data.get("stop_loss")
        annotated_b64 = None
        
        try:
            annotated_chart_path = MarketDataService.plot_chart(
                df, clean_ticker, timeframe, target=target_price, stop_loss=stop_loss_price
            )
            with open(annotated_chart_path, "rb") as image_file:
                annotated_b64 = base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            print(f"Failed to generate annotated chart: {e}")

        # Build structured response
        response_data = AIAnalysisResponse(
            signal=ai_data.get("signal", "CONFLICT"),
            confidence=ai_data.get("confidence", 0),
            reasons=ai_data.get("reasons") or ["Analysis completed."],
            bull_factors=ai_data.get("bull_factors") or [],
            bear_factors=ai_data.get("bear_factors") or [],
            pattern_names=patterns,
            concept_names=concepts,
            educational_explanations=edu_explanations,
            wait_duration_recommendation=ai_data.get("wait_duration_recommendation"),
            stop_loss=ai_data.get("stop_loss"),
            target=ai_data.get("target"),
            time_horizon=ai_data.get("time_horizon"),
            expiration_time=ai_data.get("expiration_time"),
            invalidation_conditions=ai_data.get("invalidation_conditions") or [],
            additional_comments=ai_data.get("additional_comments"),
            current_price=ind_dict.get("close", 0.0),
            annotated_chart_base64=annotated_b64
        )
        
        # 6. Save to Trade Journal (DB)
        new_trade = Trade(
            asset=asset,
            timeframe=timeframe,
            screenshot_path=tmp_path, # Ideally move this to a permanent uploads folder
            indicators=json.dumps(ind_dict),
            pattern=", ".join(patterns),
            decision=response_data.signal,
            confidence=response_data.confidence,
            reason="; ".join(response_data.reasons),
            educational_concepts=json.dumps([e.model_dump() for e in edu_explanations]),
            bull_factors=json.dumps(response_data.bull_factors),
            bear_factors=json.dumps(response_data.bear_factors)
        )
        db.add(new_trade)
        db.commit()
        db.refresh(new_trade)
        
        return response_data
        
    finally:
        # Note: in a real app, if you want to keep the image for the journal, 
        # you would move tmp_path to a permanent location.
        pass

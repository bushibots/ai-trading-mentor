from typing import List
from app.schemas.response import EducationalConcept

class EducationService:
    # A simplified knowledge base. In reality, this would be in a DB or larger JSON file.
    CONCEPT_KNOWLEDGE = {
        "Bullish Engulfing": {
            "explanation": "A two-candle pattern where a smaller red candle is completely 'engulfed' by a larger green candle.",
            "real_world_usage": "Traders use this as a strong signal of a potential reversal from a downtrend to an uptrend.",
            "advantages": "Easy to spot, strong psychological shift in momentum.",
            "disadvantages": "Can be a false signal if it occurs in the middle of a strong downtrend without other confluence.",
            "common_mistakes": "Trading it blindly without checking support levels or volume.",
            "risk": "Medium. Needs confirmation from the next candle."
        },
        "RSI Divergence": {
            "explanation": "When the price makes a new lower low, but the RSI indicator makes a higher low.",
            "real_world_usage": "Used to anticipate a loss in downward momentum and a potential bullish reversal.",
            "advantages": "Can catch trend reversals early.",
            "disadvantages": "Price can remain divergent for a long time during strong trends.",
            "common_mistakes": "Acting too early before price confirms the reversal.",
            "risk": "High if traded without price action confirmation."
        }
    }

    @staticmethod
    def enrich_with_education(patterns: List[str]) -> List[EducationalConcept]:
        """
        Takes a list of patterns/concepts identified by the AI and attaches detailed educational info.
        """
        educational_breakdown = []
        for pattern in patterns:
            # Simple matching logic, can be expanded to semantic search
            matched_key = next((k for k in EducationService.CONCEPT_KNOWLEDGE.keys() if k.lower() in pattern.lower()), None)
            
            if matched_key:
                info = EducationService.CONCEPT_KNOWLEDGE[matched_key]
                concept = EducationalConcept(
                    concept_name=matched_key,
                    explanation=info["explanation"],
                    real_world_usage=info["real_world_usage"],
                    advantages=info.get("advantages"),
                    disadvantages=info.get("disadvantages"),
                    common_mistakes=info.get("common_mistakes"),
                    risk=info.get("risk")
                )
                educational_breakdown.append(concept)
            else:
                # Fallback if concept is not in knowledge base, could ask AI to generate this later
                educational_breakdown.append(EducationalConcept(
                    concept_name=pattern,
                    explanation="Pattern identified, but detailed educational breakdown is not currently in the local knowledge base.",
                    real_world_usage="Varies depending on context."
                ))
                
        return educational_breakdown

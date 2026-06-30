from abc import ABC, abstractmethod
from typing import Dict, Any

class AIProviderBase(ABC):
    @abstractmethod
    async def analyze_chart(self, image_path: str, timeframe: str, indicators: Dict[str, Any]) -> str:
        """
        Takes an image path, timeframe, and local indicators, and returns a JSON string
        that matches the AIAnalysisResponse schema.
        """
        pass

import pandas as pd

class IndicatorService:
    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> dict:
        """
        Calculate local indicators using plain pandas.
        Expects a DataFrame with 'close'.
        """
        if df.empty or len(df) < 20:
            return {}
            
        # Normalize columns to lowercase to handle both 'Close' and 'close' formats
        df_lower = df.copy()
        df_lower.columns = [c.lower() for c in df_lower.columns]
            
        # EMA 9
        df_lower['EMA_9'] = df_lower['close'].ewm(span=9, adjust=False).mean()
        # EMA 21
        df_lower['EMA_21'] = df_lower['close'].ewm(span=21, adjust=False).mean()
        
        # RSI 14
        delta = df_lower['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df_lower['RSI_14'] = 100 - (100 / (1 + rs))
        
        latest = df_lower.iloc[-1]
        
        return {
            "ema_9": float(latest.get("EMA_9", 0)),
            "ema_21": float(latest.get("EMA_21", 0)),
            "rsi_14": float(latest.get("RSI_14", 0)),
            "trend": "bullish" if latest.get("EMA_9", 0) > latest.get("EMA_21", 0) else "bearish"
        }

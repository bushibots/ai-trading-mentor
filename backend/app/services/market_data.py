import yfinance as yf
import mplfinance as mpf
import pandas as pd
import tempfile
import os
from typing import Tuple, Dict, Optional

class MarketDataService:
    @staticmethod
    def fetch_data(asset: str, timeframe: str) -> Tuple[pd.DataFrame, Dict, str]:
        # Map frontend timeframes to yfinance valid intervals
        tf_map = {
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "4h": "1h",
            "12h": "1h",
            "24h": "1d"
        }
        interval = tf_map.get(timeframe, "1d")
        
        # Heuristic to convert user input to yfinance ticker format
        ticker = asset.upper().replace("/", "-").replace("USDT", "USD")
        if not "-" in ticker and ticker.endswith("USD"):
             ticker = ticker[:-3] + "-USD"
        elif not "-" in ticker and not ticker.endswith("USD"):
             pass

        period = "1mo" if interval == "1d" else "7d"
        
        import requests
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://finance.yahoo.com/'
        })
        
        df = yf.download(ticker, period=period, interval=interval, progress=False, session=session)
        
        if df.empty:
            raise ValueError(f"Could not fetch data for {asset} at {interval}. Try using formats like 'BTC-USD' or 'AAPL'.")
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required):
            raise ValueError("Incomplete OHLCV data from provider.")

        last_row = df.iloc[-1]
        indicators = {
            "close": float(last_row['Close']),
            "volume": float(last_row['Volume']) if not pd.isna(last_row['Volume']) else 0
        }
        return df.tail(100), indicators, ticker

    @staticmethod
    def plot_chart(df: pd.DataFrame, ticker: str, timeframe: str, target: Optional[float] = None, stop_loss: Optional[float] = None) -> str:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_path = temp_file.name
        temp_file.close()
        
        kwargs = dict(type='candle', style='charles', savefig=temp_path, title=f"{ticker} ({timeframe})")
        if df['Volume'].sum() > 0:
            kwargs['volume'] = True
            
        hlines = []
        colors = []
        
        if target is not None:
            hlines.append(target)
            colors.append('g')
            
        if stop_loss is not None:
            hlines.append(stop_loss)
            colors.append('r')
            
        if hlines:
            kwargs['hlines'] = dict(hlines=hlines, colors=colors, linestyle='--', linewidths=2)
            
        mpf.plot(df, **kwargs)
        
        return temp_path

import requests

def test_symbol(symbol):
    print(f"Testing analysis for {symbol}...")
    try:
        res = requests.post(
            "http://127.0.0.1:8000/api/v1/analyze/analyze", 
            data={"asset": symbol, "timeframe": "1h", "user_notes": "Testing multi-asset functionality"}
        )
        print("Status:", res.status_code)
        if res.status_code == 200:
            data = res.json()
            print("Signal:", data.get("signal"))
            print("Confidence:", data.get("confidence"))
            print("Current Price:", data.get("current_price"))
            print("Reasons:", data.get("reasons"))
        else:
            print("Error Details:", res.text)
    except Exception as e:
        print("Failed to request:", e)

test_symbol("EURUSD=X")
print("-" * 40)
test_symbol("AAPL")

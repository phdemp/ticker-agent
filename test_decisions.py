import asyncio
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, 'src')
load_dotenv()

from trader.strategy_manager import StrategyManager

async def test_decisions():
    print("--- Testing Bot Decisions ---")
    s = StrategyManager()
    
    ticker = "$SOL"
    technicals = {
        "price": 150.0,
        "rsi": 25.0, # Oversold -> Should trigger buy
        "macd": {"macd": 1.5, "signal": 1.0, "hist": 0.5}
    }
    news_summary = "Solana sees massive inflow of institutional capital. Network activity at all time high."
    
    print(f"Testing with: {ticker}, RSI={technicals['rsi']}, News='{news_summary}'")
    
    decisions = await s.get_decisions(ticker, technicals, news_summary)
    
    print(f"\nReceived {len(decisions)} decisions:")
    for d in decisions:
        print(f"🤖 {d['bot_id']}:\n   Action: {d['action']}\n   Confidence: {d['confidence']}%\n   Reason: {d['reason']}\n")
        
    if len(decisions) == 5:
        print("✅ All bots responded!")
    else:
        print(f"⚠️ expected 5 decisions, got {len(decisions)}")

if __name__ == "__main__":
    asyncio.run(test_decisions())

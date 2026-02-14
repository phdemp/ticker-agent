
import asyncio
import os
from dotenv import load_dotenv
from loguru import logger
import sys

# Add src to path
sys.path.append('src')

from trader.strategy_manager import StrategyManager, DEFAULT_MODELS

async def debug_all_bots():
    load_dotenv()
    manager = StrategyManager()
    
    print("\n--- Diagnostic: Testing All Bots ---\n")
    
    ticker = "SOL"
    technicals = {"price": 150, "rsi": 25, "macd": 2.5, "ema": 130, "volume_z": 5.0}
    news_summary = "MASSIVE WHALE ALERT: $500M in SOL moved from exchange to cold wallet. Sentiment is extremely high despite oversold conditions."
    
    # We'll call get_decisions which asks all active bots
    decisions = await manager.get_decisions(ticker, technicals, news_summary)
    
    print(f"\nTotal Decisions Received: {len(decisions)}\n")
    
    active_bot_ids = [d['bot_id'] for d in decisions]
    
    for bot_id in DEFAULT_MODELS.keys():
        provider, model = DEFAULT_MODELS[bot_id]
        status = "✅ ACTIVE" if bot_id in active_bot_ids else "❌ FAILED"
        print(f"[{status}] {bot_id} ({provider} -> {model})")
        
        if bot_id in active_bot_ids:
            decision = next(d for d in decisions if d['bot_id'] == bot_id)
            print(f"   - Action: {decision['action']}")
            print(f"   - Confidence: {decision['confidence']}")
            print(f"   - Rationale: {decision['reason']}")
            print(f"   --- RAW OUTPUT ---")
            print(decision['raw_output'])
            print(f"   --- END RAW ---")
        else:
            # Check if it was even initialized
            if bot_id not in manager.bots:
                print(f"   - Error: Provider not initialized (Missing Key?)")
            else:
                print(f"   - Error: Generation failed (Check logs for API error)")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(debug_all_bots())

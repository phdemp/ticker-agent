import asyncio
import sys
import os
from loguru import logger

# Add src to path
sys.path.append('src')

from trader.paper import PaperTrader
from db import init_db

async def reproduce():
    print("Testing Portfolio Update Logic...")
    init_db()
    trader = PaperTrader()
    
    # Mock analyzed_tokens
    analyzed_tokens = [
        {'ticker': '$BCH', 'price': 303.17},
        {'ticker': '$STX', 'price': 0.8884}
    ]
    
    try:
        print("1. Constructing current_prices...")
        current_prices = {}
        for t in analyzed_tokens:
            current_prices[t['ticker'].replace("$", "").upper()] = t['price']
        print(f"Current Prices: {current_prices}")
        
        print("2. Calling trader.check_trades...")
        trader.check_trades(current_prices)
        
        print("3. Fetching portfolio data...")
        portfolio_data = {
            "balance_usd": trader.get_balance("USD"),
            "active_trades": trader.get_active_trades()
        }
        print(f"Portfolio Data Result: {portfolio_data}")
        
    except Exception as e:
        print(f"!!! FAILURE !!!: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reproduce())

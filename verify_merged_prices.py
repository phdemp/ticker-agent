
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from scrapers.dexscreener import DexScreenerScraper
from scrapers.coinmarketcap import CoinMarketCapScraper

async def verify_merged_logic():
    load_dotenv()
    dex = DexScreenerScraper()
    cmc = CoinMarketCapScraper()
    
    test_tickers = ["$BTC", "$ETH", "$SOL", "$JUP", "$PYTH"]
    
    print(f"{'Ticker':<10} | {'CMC (Anchor)':<15} | {'Dex (Raw)':<15} | {'Final Used':<15} | {'Status'}")
    print("-" * 75)
    
    # Simulate the logic in main.py
    cmc_quotes = await cmc.get_quotes(test_tickers)
    
    for ticker in test_tickers:
        cmc_data = cmc_quotes.get(ticker)
        
        search_query = ticker.lstrip("$")
        pair_data = await dex.scrape(search_query, limit=1)
        pair = pair_data[0] if pair_data else {}
        
        dex_price = float(pair.get("price", 0) or 0)
        
        # Merged Logic from main.py
        if cmc_data:
            current_price = cmc_data['price']
            source = "CMC"
        else:
            current_price = dex_price
            source = "DEX"
            
        status = "✅ CORRECT (Anchored)" if source == "CMC" else "⚠️ FALLBACK"
        
        print(f"{ticker:<10} | {cmc_data['price'] if cmc_data else 0.0:<15.2f} | {dex_price:<15.2f} | {current_price:<15.2f} | {status}")

if __name__ == "__main__":
    asyncio.run(verify_merged_logic())

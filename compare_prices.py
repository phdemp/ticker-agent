
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from scrapers.dexscreener import DexScreenerScraper
from scrapers.coinmarketcap import CoinMarketCapScraper

async def verify_prices():
    load_dotenv()
    dex = DexScreenerScraper()
    cmc = CoinMarketCapScraper()
    
    # We'll check the main ones
    test_tickers = ["BTC", "ETH", "SOL", "JUP", "PYTH"]
    
    print(f"{'Ticker':<10} | {'DexScreener':<15} | {'CoinMarketCap':<15} | {'Diff %':<10}")
    print("-" * 60)
    
    # CMC fetch latest for many is more efficient
    # But for a small test, let's just use what we have or adapt
    # The existing CMC scraper only gets top tokens based on market cap listings.
    # Let's write a quick inline fetch for CMC price for these specific symbols.
    
    import aiohttp
    cmc_key = os.getenv("COINMARKETCAP_API_KEY")
    headers = {'X-CMC_PRO_API_KEY': cmc_key, 'Accept': 'application/json'}
    
    async with aiohttp.ClientSession() as session:
        # Get CMC prices for all test tickers in one go
        symbols_str = ",".join(test_tickers)
        cmc_url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbols_str}"
        
        async with session.get(cmc_url, headers=headers) as resp:
            cmc_data = await resp.json()
            
        for ticker in test_tickers:
            # DexScreener
            dex_data = await dex.scrape(ticker, limit=1)
            dex_price = float(dex_data[0]['price']) if dex_data else 0.0
            
            # CMC
            try:
                cmc_price = cmc_data['data'][ticker]['quote']['USD']['price']
            except:
                cmc_price = 0.0
            
            diff_pct = abs(dex_price - cmc_price) / cmc_price * 100 if cmc_price > 0 else 0
            
            print(f"{ticker:<10} | {dex_price:<15.4f} | {cmc_price:<15.4f} | {diff_pct:<10.2f}%")

if __name__ == "__main__":
    asyncio.run(verify_prices())

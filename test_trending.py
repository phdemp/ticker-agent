import asyncio
from src.scrapers.coingecko import CoinGeckoScraper

async def test():
    scraper = CoinGeckoScraper()
    trending = await scraper.get_trending_details()
    
    print(f"Fetched {len(trending)} trending coins")
    print("\nFirst 3 coins:")
    for coin in trending[:3]:
        print(f"  {coin['symbol']}: {coin['name']} (Rank: {coin['market_cap_rank']})")
        print(f"    Thumb: {coin['thumb'][:50]}...")

asyncio.run(test())

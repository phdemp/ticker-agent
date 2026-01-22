
import asyncio
from src.scrapers.dexscreener import DexScreenerScraper
from src.scrapers.cointelegraph import CointelegraphScraper
from src.ml.sentiment import SentimentAnalyzer

async def main():
    print("--- Testing DexScreener ---")
    dex = DexScreenerScraper()
    tickers = ["SOL", "BONK", "WEN"]
    
    for ticker in tickers:
        print(f"\nSearching for {ticker}...")
        data = await dex.scrape(ticker, limit=1)
        if data:
            pair = data[0]
            print(f"Ticker: {pair.get('ticker')}")
            print(f"Name: {pair.get('name')}")
            print(f"Price: {pair.get('price')}")
            print(f"FDV: {pair.get('metadata', {}).get('fdv')}")
            print(f"Liquidity: {pair.get('metadata', {}).get('liquidity')}")
            print(f"Pair Address: {pair.get('metadata', {}).get('pairAddress')}")
        else:
            print("No data found.")

    print("\n--- Testing Sentiment ---")
    ct = CointelegraphScraper()
    news = await ct.scrape(limit=5)
    print(f"Fetched {len(news)} articles.")
    
    analyzer = SentimentAnalyzer()
    for n in news:
        print(f"Title: {n['metadata']['title']}")
        sentiment = analyzer.analyze(n['content'])
        print(f"Sentiment: {sentiment}")

if __name__ == "__main__":
    asyncio.run(main())

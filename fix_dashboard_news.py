
import asyncio
import sys
import os
import traceback

# Add src to path
sys.path.append(os.path.abspath("src"))

async def main():
    with open("execution.log", "w") as f:
        try:
            f.write("Starting fix script...\n")
            from scrapers.cointelegraph import CointelegraphScraper
            from dashboard import generate_dashboard
            
            f.write("Imported modules.\n")
            
            scraper = CointelegraphScraper()
            news = await scraper.scrape(limit=10)
            
            f.write(f"Fetched {len(news)} articles.\n")
            
            for article in news:
                img = article['metadata']['image']
                f.write(f"Image: {img}\n")
            
            generate_dashboard(news=news)
            f.write("Dashboard updated.\n")
            
        except Exception:
            f.write(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())

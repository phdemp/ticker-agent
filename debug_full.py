
import asyncio
import sys
import os
import traceback

# Add src to path
sys.path.append(os.path.abspath("src"))

async def test():
    with open("debug_scraper_full.txt", "w") as f:
        try:
            from scrapers.cointelegraph import CointelegraphScraper
            f.write("Imported Scraper\n")
            
            scraper = CointelegraphScraper()
            f.write("Initialized Scraper. Fetching...\n")
            
            # Test full scrape
            news = await scraper.scrape(limit=5)
            f.write(f"Scraped {len(news)} items\n")
            
            for i, item in enumerate(news):
                title = item['metadata']['title']
                img = item['metadata']['image']
                f.write(f"Item {i}: {title}\n")
                f.write(f"  Image: {img}\n")
                
                if "s3.cointelegraph.com" in str(img):
                    f.write("  -> VERIFIED FIXED URL\n")
                else:
                    f.write("  -> WARNING: URL NOT FIXED or NOT S3\n")
                    
        except Exception:
            f.write(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test())

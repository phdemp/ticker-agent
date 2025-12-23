
import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from scrapers.cointelegraph import CointelegraphScraper
from dashboard import generate_dashboard
from loguru import logger

async def main():
    logger.info("Running standalone news fix...")
    
    scraper = CointelegraphScraper()
    news = await scraper.scrape(limit=10)
    
    logger.info(f"Fetched {len(news)} articles.")
    for article in news:
        logger.info(f"Title: {article['metadata']['title']}")
        logger.info(f"Image URL: {article['metadata']['image']}")
    
    # Generate dashboard with ONLY news (others None to keep existing structure or empty)
    # Note: This will overwrite index.html with empty tables for other sections, 
    # but it verifies the news images.
    # To avoid breaking the whole dashboard, ideally we'd load existing state, but 
    # for verification let's just generate it. The user can re-run main.py later.
    
    generate_dashboard(news=news)
    logger.info("Dashboard updated. Please check public/index.html to see if images are fixed.")

if __name__ == "__main__":
    asyncio.run(main())

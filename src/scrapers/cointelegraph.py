from typing import List, Dict, Any
import feedparser
from .base import BaseScraper
from loguru import logger

class CointelegraphScraper(BaseScraper):
    def __init__(self):
        super().__init__("Cointelegraph")
        self.rss_url = "https://cointelegraph.com/rss"

    async def scrape(self, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetches latest news from Cointelegraph RSS feed.
        Query is ignored as RSS provides latest news.
        """
        try:
            # RSS fetching is synchronous, but fast. 
            # In a full async app, we might want to run this in an executor, 
            # but for this scale it's fine or we can use httpx to fetch raw XML and parse.
            
            # Using httpx to keep it async-friendly
            response = await self.client.get(self.rss_url)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                return self._process_feed(feed.entries, limit)
            else:
                self.log_error(f"RSS fetch failed: {response.status_code}")
                return []
        except Exception as e:
            self.log_error(f"Scrape error: {e}")
            return []

    def _process_feed(self, entries: List[Any], limit: int) -> List[Dict[str, Any]]:
        results = []
        for entry in entries[:limit]:
            # Extract tags if available
            tags = [tag.term for tag in entry.get('tags', [])]
            
            # Extract image
            image_url = None
            if 'media_content' in entry:
                image_url = entry.media_content[0].get('url')
            elif 'enclosures' in entry:
                image_url = entry.enclosures[0].get('href')
            
            results.append({
                "platform": "cointelegraph",
                "user": entry.get("author", "Cointelegraph"),
                "content": f"{entry.title} - {entry.description}",
                "timestamp": entry.get("published"),
                "url": entry.link,
                "metadata": {
                    "title": entry.title,
                    "summary": entry.description,
                    "tags": tags,
                    "image": image_url
                }
            })
        return results

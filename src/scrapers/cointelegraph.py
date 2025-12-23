import base64
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

    def _extract_original_image_url(self, proxy_url: str) -> str:
        """
        Attempts to extract the original S3 URL from the Cointelegraph proxy URL.
        Proxy URL format often looks like: 
        https://images.cointelegraph.com/images/528_{BASE64_ENCODED_URL}.jpg
        """
        if not proxy_url:
            return None
            
        try:
            # Check if it looks like the proxy URL we know
            if "images.cointelegraph.com/images" in proxy_url and "_" in proxy_url:
                # Extract the base64 part: everything between the first '_' and the last '.'
                # Example: .../images/528_aHR0cHM... .jpg
                
                # Split by last '/' to get filename
                filename = proxy_url.split('/')[-1]
                
                # Find the underscore separating size and content
                if '_' in filename:
                    parts = filename.split('_', 1)
                    if len(parts) == 2:
                        b64_part = parts[1]
                        # Remove file extension if present (though base64 decoding might handle it if padding is correct, better safe)
                        if '.' in b64_part:
                            b64_part = b64_part.rsplit('.', 1)[0]
                            
                        # Fix padding if necessary (len must be multiple of 4)
                        padding = len(b64_part) % 4
                        if padding:
                            b64_part += '=' * (4 - padding)
                            
                        # Decode
                        decoded_url = base64.urlsafe_b64decode(b64_part).decode('utf-8')
                        
                        # Verify it looks like a URL
                        if decoded_url.startswith('http'):
                            return decoded_url
        except Exception:
            # If anything fails, return the original or None, but let's stick to original 
            # so we don't break working ones that we just failed to parse.
            pass
            
        return proxy_url

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
            
            # Fix broken proxy URLs
            if image_url:
                image_url = self._extract_original_image_url(image_url)
            
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

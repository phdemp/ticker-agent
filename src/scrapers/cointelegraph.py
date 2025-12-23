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
            if "images.cointelegraph.com/images" in proxy_url:
                # The Base64 string is usually the longest part of the filename
                filename = proxy_url.split('/')[-1]
                
                # Remove extension
                if '.' in filename:
                    filename = filename.rsplit('.', 1)[0]
                
                # Split by underscore. The base64 part should be the last part usually, 
                # or we can try to decode each part.
                parts = filename.split('_')
                
                # Iterate through parts to find the one that decodes to a valid URL
                for part in parts:
                    if len(part) < 20: # Skip short parts like "528"
                        continue
                        
                    try:
                        # Fix padding
                        padding = len(part) % 4
                        if padding:
                            part += '=' * (4 - padding)
                            
                        # Try decoding with standard b64decode (more common for this usage)
                        # We use standard because the string might contain '+' or '/' mapped to base64 chars
                        # URLSafe is alternate alphabet. Let's try both if one fails.
                        decoded = None
                        try:
                            decoded = base64.urlsafe_b64decode(part).decode('utf-8')
                        except:
                            decoded = base64.b64decode(part).decode('utf-8')
                            
                        if decoded and decoded.startswith('http'):
                            return decoded
                    except:
                        continue
        except Exception:
            pass
            
        return proxy_url

    def _process_feed(self, entries: List[Any], limit: int) -> List[Dict[str, Any]]:
        from bs4 import BeautifulSoup
        
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
            
            # Clean summary text (remove HTML tags)
            summary_text = entry.description
            try:
                soup = BeautifulSoup(entry.description, "html.parser")
                summary_text = soup.get_text(separator=' ', strip=True)
            except Exception as e:
                self.log_error(f"Error cleaning summary: {e}")

            results.append({
                "platform": "cointelegraph",
                "user": entry.get("author", "Cointelegraph"),
                "content": f"{entry.title} - {summary_text}",
                "timestamp": entry.get("published"),
                "url": entry.link,
                "metadata": {
                    "title": entry.title,
                    "summary": summary_text,
                    "tags": tags,
                    "image": image_url
                }
            })
        return results

import random
from typing import List, Dict, Any
from lxml import etree
from .base import BaseScraper

# List of public Nitter instances
NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.lucabased.xyz",
    "https://nitter.privacydev.net",
    "https://light.nitter.net",
    "https://nitter.net",
    "https://nitter.esmailelbob.xyz",
    "https://nitter.uni-sonia.com",
    "https://nitter.ktachibana.party",
    "https://nitter.tmoe.name",
    "https://nitter.dafriser.net",
]

class NitterScraper(BaseScraper):
    def __init__(self):
        super().__init__("Nitter")

    async def scrape(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Scrapes Twitter via Nitter RSS.
        Query can be a cashtag (e.g., "$AAPL") or a user handle.
        """
        # Clean query
        query = query.replace("$", "%24") # URL encode $
        
        results = []
        # Try random instances until one works
        random.shuffle(NITTER_INSTANCES)
        
        for instance in NITTER_INSTANCES:
            try:
                url = f"{instance}/search/rss?f=tweets&q={query}"
                response = await self.client.get(url)
                
                if response.status_code == 200:
                    results = self._parse_rss(response.content)
                    if results:
                        break # Found data, stop trying instances
            except Exception as e:
                self.log_error(f"Failed to scrape {instance}: {e}")
                continue
                
        return results[:limit]

    def _parse_rss(self, content: bytes) -> List[Dict[str, Any]]:
        items = []
        try:
            root = etree.fromstring(content)
            # Handle namespaces if present, usually Nitter RSS is simple
            for item in root.findall(".//item"):
                title = item.find("title").text if item.find("title") is not None else ""
                description = item.find("description").text if item.find("description") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                creator = item.find("dc:creator", namespaces=root.nsmap).text if item.find("dc:creator", namespaces=root.nsmap) is not None else "Unknown"
                link = item.find("link").text if item.find("link") is not None else ""
                
                items.append({
                    "platform": "twitter",
                    "user": creator,
                    "content": title, # Nitter RSS title is often the tweet text
                    "timestamp": pub_date,
                    "url": link,
                    "metadata": {"full_text": description}
                })
        except Exception as e:
            self.log_error(f"RSS Parsing error: {e}")
            
        return items

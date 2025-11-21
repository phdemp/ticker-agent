from abc import ABC, abstractmethod
from typing import List, Dict, Any
import httpx
from loguru import logger

class BaseScraper(ABC):
    def __init__(self, name: str):
        self.name = name
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def close(self):
        await self.client.aclose()

    @abstractmethod
    async def scrape(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Scrape data for a given query.
        
        Args:
            query: The ticker or search term (e.g., "$AAPL", "BTC").
            limit: Max number of items to fetch.
            
        Returns:
            A list of dictionaries containing scraped data.
        """
        pass

    def log_error(self, error: Exception):
        logger.error(f"[{self.name}] Error: {error}")

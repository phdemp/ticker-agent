import aiohttp
from loguru import logger
from typing import List, Dict, Optional
import os

class CoinMarketCapScraper:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("COINMARKETCAP_API_KEY")
        self.base_url = "https://pro-api.coinmarketcap.com"
        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }

    async def get_top_tokens(self, limit: int = 100) -> List[str]:
        """
        Fetches the top N cryptocurrencies by market cap.
        Returns a list of ticker symbols (e.g., ['$BTC', '$ETH']).
        """
        if not self.api_key:
            logger.warning("CoinMarketCap API key not found. Skipping CMC fetch.")
            return []

        url = f"{self.base_url}/v1/cryptocurrency/listings/latest"
        params = {
            'start': '1',
            'limit': str(limit),
            'convert': 'USD',
            'sort': 'market_cap'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        tokens = []
                        for item in data.get('data', []):
                            symbol = item.get('symbol')
                            if symbol:
                                tokens.append(f"${symbol}")
                        
                        logger.info(f"Fetched {len(tokens)} tokens from CoinMarketCap.")
                        return tokens
                    else:
                        error_msg = await response.text()
                        logger.error(f"CMC API Error {response.status}: {error_msg}")
                        return []
        except Exception as e:
            logger.error(f"Failed to fetch from CoinMarketCap: {e}")
            return []

if __name__ == "__main__":
    # Test script
    import asyncio
    async def test():
        # You can pass the key directly for testing if env is not set
        # scraper = CoinMarketCapScraper(api_key="YOUR_KEY") 
        scraper = CoinMarketCapScraper() # Assumes env var is set
        tokens = await scraper.get_top_tokens(limit=10)
        print("Top 10 Tokens:", tokens)

    # from dotenv import load_dotenv
    # load_dotenv()
    # asyncio.run(test())

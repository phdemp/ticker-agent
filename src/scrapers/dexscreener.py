from typing import List, Dict, Any
from .base import BaseScraper

class DexScreenerScraper(BaseScraper):
    def __init__(self):
        super().__init__("DexScreener")
        self.api_url = "https://api.dexscreener.com/latest/dex/search"

    async def scrape(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetches token data from DexScreener.
        Query should be a token symbol or address.
        """
        try:
            response = await self.client.get(self.api_url, params={"q": query})
            if response.status_code == 200:
                data = response.json()
                pairs = data.get("pairs", [])
                return self._process_pairs(pairs, limit)
            else:
                self.log_error(f"API Error: {response.status_code}")
                return []
        except Exception as e:
            self.log_error(f"Scrape error: {e}")
            return []

    async def get_token_boosts(self) -> List[Dict[str, Any]]:
        """
        Fetches the latest boosted tokens from DexScreener.
        Returns a list of dicts with 'chainId' and 'tokenAddress'.
        """
        try:
            url = "https://api.dexscreener.com/token-boosts/top/v1"
            response = await self.client.get(url)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            self.log_error(f"Boosts fetch error: {e}")
            return []

    def _process_pairs(self, pairs: List[Dict], limit: int) -> List[Dict[str, Any]]:
        results = []
        for pair in pairs[:limit]:
            results.append({
                "platform": "dexscreener",
                "user": "market",
                "content": f"Price: {pair.get('priceUsd')} | Vol24h: {pair.get('volume', {}).get('h24')}",
                "timestamp": None, # Real-time
                "url": pair.get("url"),
                "metadata": {
                    "chainId": pair.get("chainId"),
                    "symbol": pair.get("baseToken", {}).get("symbol"),
                    "tokenAddress": pair.get("baseToken", {}).get("address"),
                    "liquidity": pair.get("liquidity", {}).get("usd"),
                    "fdv": pair.get("fdv"),
                    "txns": pair.get("txns", {}).get("h24")
                }
            })
        return results

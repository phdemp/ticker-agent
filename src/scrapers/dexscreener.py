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
            # Extract basic info
            base_token = pair.get("baseToken", {})
            info = pair.get("info", {})
            
            # Extract expanded metrics
            price_change = pair.get("priceChange", {})
            txns = pair.get("txns", {}).get("h24", {})
            liquidity = pair.get("liquidity", {})
            
            results.append({
                "platform": "dexscreener",
                "ticker": base_token.get("symbol"), # Add top level ticker for ease
                "name": base_token.get("name"),
                "logo": info.get("imageUrl"), 
                "price": pair.get("priceUsd"),
                "price_change": {
                    "h1": price_change.get("h1", 0),
                    "h6": price_change.get("h6", 0),
                    "h24": price_change.get("h24", 0),
                },
                "volume_profile": {
                    "buys": txns.get("buys", 0),
                    "sells": txns.get("sells", 0),
                },
                "url": pair.get("url"),
                "metadata": {
                    "chainId": pair.get("chainId"),
                    "tokenAddress": base_token.get("address"),
                    "liquidity": liquidity.get("usd"),
                    "fdv": pair.get("fdv"),
                    "pairAddress": pair.get("pairAddress")
                }
            })
        return results

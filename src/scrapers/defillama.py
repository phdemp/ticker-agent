from typing import List, Dict, Any
from .base import BaseScraper

class DeFiLlamaScraper(BaseScraper):
    def __init__(self):
        super().__init__("DeFiLlama")
        self.base_url = "https://api.llama.fi"
        self.yields_url = "https://yields.llama.fi"
        self.stablecoins_url = "https://stablecoins.llama.fi"

    async def scrape(self, query: str = "", limit: int = 5) -> Dict[str, Any]:
        """
        Fetches global DeFi stats. Query is ignored as this is global data.
        Returns a dict with 'tvl', 'yields', and 'stablecoins'.
        """
        results = {
            "tvl": 0,
            "yields": [],
            "stablecoins": 0
        }
        
        try:
            # 1. Global TVL
            tvl_resp = await self.client.get(f"{self.base_url}/v2/chains")
            if tvl_resp.status_code == 200:
                chains = tvl_resp.json()
                results["tvl"] = sum(c.get("tvl", 0) for c in chains)
            
            # 2. Top Yields
            yields_resp = await self.client.get(f"{self.yields_url}/pools")
            if yields_resp.status_code == 200:
                data = yields_resp.json()
                pools = data.get("data", [])
                # Filter TVL > 1M and sort by APY
                top_pools = sorted(
                    [p for p in pools if p.get('tvlUsd', 0) > 1_000_000], 
                    key=lambda x: x.get('apy', 0), 
                    reverse=True
                )[:limit]
                
                results["yields"] = [{
                    "project": p.get("project"),
                    "symbol": p.get("symbol"),
                    "chain": p.get("chain"),
                    "apy": p.get("apy"),
                    "tvl": p.get("tvlUsd")
                } for p in top_pools]

            # 3. Stablecoins
            stable_resp = await self.client.get(f"{self.stablecoins_url}/stablecoins?includePrices=true")
            if stable_resp.status_code == 200:
                data = stable_resp.json()
                pegged = data.get("peggedAssets", [])
                results["stablecoins"] = sum(p.get("circulating", {}).get("peggedUSD", 0) or 0 for p in pegged)
                
        except Exception as e:
            self.log_error(f"Scrape error: {e}")
            
        return [results] # Return as list to match BaseScraper interface

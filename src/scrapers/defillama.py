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
            
    async def get_stablecoin_chains(self) -> List[Dict[str, Any]]:
        """
        Fetches stablecoin market cap and 7d change by chain.
        Returns list of dicts: {'chain': 'Solana', 'total': 123456, 'change_7d': 5000, 'pct_7d': 5.2}
        """
        results = {}
        
        try:
            # Fetch all stablecoins with price/chain data
            url = f"{self.stablecoins_url}/stablecoins?includePrices=true"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                pegged = data.get("peggedAssets", [])
                
                # We want to aggregate by chain
                chain_stats = {} 
                
                for asset in pegged:
                    # check if significant (e.g. > $10m mcap) to avoid noise
                    if asset.get("circulating", {}).get("peggedUSD", 0) < 10_000_000:
                        continue
                        
                    # chainCirculating is a dict: { "Ethereum": { "current": {...}, "circulatingPrevWeek": {...} } }
                    chain_data = asset.get("chainCirculating", {})
                    
                    for chain_name, periods in chain_data.items():
                        current_amt = periods.get("current", {}).get("peggedUSD", 0) or 0
                        prev_week_amt = periods.get("circulatingPrevWeek", {}).get("peggedUSD", 0) or 0
                        
                        if chain_name not in chain_stats:
                            chain_stats[chain_name] = {"current": 0.0, "prev_week": 0.0}
                        
                        chain_stats[chain_name]["current"] += current_amt
                        chain_stats[chain_name]["prev_week"] += prev_week_amt
                
                # Calculate changes
                final_list = []
                for chain, stats in chain_stats.items():
                   curr = stats["current"]
                   prev = stats["prev_week"]
                   if curr > 0: # Only active chains
                       change_7d = curr - prev
                       pct_7d = (change_7d / prev * 100) if prev > 0 else 0
                       
                       # Filter out tiny chains or errors
                       if curr > 1_000_000:
                           final_list.append({
                               "chain": chain,
                               "total": curr,
                               "change_7d": change_7d,
                               "pct_7d": pct_7d
                           })
                
                # Sort by 7d change (growth)
                final_list.sort(key=lambda x: x["change_7d"], reverse=True)
                return final_list

        except Exception as e:
            self.log_error(f"Stablecoin chains error: {e}")
            
        return []

    async def get_protocols(self) -> List[Dict[str, Any]]:
        """
        Fetches all protocols from DeFiLlama.
        Useful for screening top DApps by TVL.
        """
        try:
            resp = await self.client.get(f"{self.base_url}/protocols")
            if resp.status_code == 200:
                data = resp.json()
                # Sort by TVL descending
                return sorted(data, key=lambda x: x.get('tvl', 0) or 0, reverse=True)
            else:
                self.log_error(f"Protocols fetch failed: {resp.status_code}")
                return []
        except Exception as e:
            self.log_error(f"Protocols error: {e}")
            return []

    async def get_protocol(self, slug: str) -> Dict[str, Any]:
        """
        Fetches detailed data for a specific protocol.
        Slug example: 'aave', 'uniswap', 'lido'
        """
        try:
            resp = await self.client.get(f"{self.base_url}/protocol/{slug}")
            if resp.status_code == 200:
                return resp.json()
            else:
                self.log_error(f"Protocol {slug} fetch failed: {resp.status_code}")
                return {}
        except Exception as e:
            self.log_error(f"Protocol {slug} error: {e}")
            return {}

    async def get_historical_tvl(self, chain: str) -> List[Dict[str, Any]]:
        """
        Fetches historical TVL for a specific chain.
        """
        try:
            resp = await self.client.get(f"{self.base_url}/v2/historicalChainTvl/{chain}")
            if resp.status_code == 200:
                return resp.json()
            else:
                self.log_error(f"Historical TVL for {chain} failed: {resp.status_code}")
                return []
        except Exception as e:
            self.log_error(f"Historical TVL for {chain} error: {e}")
            return []

    async def get_dex_volumes(self) -> Dict[str, Any]:
        """
        Fetches DEX volume overview.
        """
        try:
            resp = await self.client.get(f"{self.base_url}/overview/dexs")
            if resp.status_code == 200:
                return resp.json()
            else:
                self.log_error(f"DEX Volumes fetch failed: {resp.status_code}")
                return {}
        except Exception as e:
            self.log_error(f"DEX Volumes error: {e}")
            return {}

    async def get_fees_revenue(self) -> Dict[str, Any]:
        """
        Fetches Fees and Revenue overview.
        """
        try:
            resp = await self.client.get(f"{self.base_url}/overview/fees")
            if resp.status_code == 200:
                return resp.json()
            else:
                self.log_error(f"Fees Revenue fetch failed: {resp.status_code}")
                return {}
        except Exception as e:
            self.log_error(f"Fees Revenue error: {e}")
            return {}

    def scrape(self, query: str = "", limit: int = 5):
        # ... (keep existing scrape wrapper or leave it be, we are adding a new method)
        return super().scrape(query, limit) # Just a placeholder if I need to touch it


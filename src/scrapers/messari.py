
import os
from typing import List, Dict, Any
from .base import BaseScraper

class MessariScraper(BaseScraper):
    def __init__(self):
        super().__init__("Messari")
        self.base_url = "https://api.messari.io"
        self.api_key = os.getenv("MESSARI_API_KEY")
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["x-messari-api-key"] = self.api_key
        return headers

    async def get_all_assets(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetches list of assets.
        Endpoint: /metrics/v2/assets
        """
        try:
            url = f"{self.base_url}/metrics/v2/assets?limit={limit}"
            resp = await self.client.get(url, headers=self._get_headers())
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", [])
            else:
                self.log_error(f"All assets fetch failed: {resp.status_code}")
                return []
        except Exception as e:
            self.log_error(f"All assets error: {e}")
            return []

    async def get_asset_details(self, asset_slugs: List[str]) -> List[Dict[str, Any]]:
        """
        Fetches detailed information for specific assets.
        Endpoint: /metrics/v2/assets/details?assets=slug1,slug2
        """
        try:
            assets_param = ",".join(asset_slugs)
            url = f"{self.base_url}/metrics/v2/assets/details?assets={assets_param}"
            resp = await self.client.get(url, headers=self._get_headers())
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", [])
            else:
                self.log_error(f"Asset details fetch failed: {resp.status_code}")
                return []
        except Exception as e:
            self.log_error(f"Asset details error: {e}")
            return []

    async def scrape(self, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Satisfies BaseScraper interface.
        If query is provided, fetch details for that asset.
        Otherwise, return list of top assets.
        """
        if query:
            # Treat query as asset slug
            return await self.get_asset_details([query])
        else:
            return await self.get_all_assets(limit)

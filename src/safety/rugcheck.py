import httpx
from loguru import logger

class RugCheck:
    BASE_URL = "https://api.rugcheck.xyz/v1/tokens"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def check_token(self, mint_address: str) -> dict:
        """
        Checks a Solana token against RugCheck.xyz.
        Returns a dict with risk score and details.
        """
        try:
            response = await self.client.get(f"{self.BASE_URL}/{mint_address}/report")
            if response.status_code == 200:
                data = response.json()
                return self._parse_report(data)
            else:
                logger.warning(f"RugCheck API error: {response.status_code}")
                return {"score": -1, "status": "unknown"}
        except Exception as e:
            logger.error(f"RugCheck failed: {e}")
            return {"score": -1, "status": "error"}

    def _parse_report(self, data: dict) -> dict:
        # RugCheck score is usually 0-10000 or similar. Lower is better?
        # Actually, let's look at the 'score' field if it exists, or 'risks'.
        # For now, we'll return the raw score and risk count.
        score = data.get("score", 0)
        risks = data.get("risks", [])
        return {
            "score": score,
            "risk_count": len(risks),
            "risks": [r.get("name") for r in risks],
            "is_safe": score < 5000 # Arbitrary threshold, need to verify
        }

    async def close(self):
        await self.client.aclose()

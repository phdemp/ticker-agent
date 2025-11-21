import httpx
from loguru import logger

class DiscordNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient()

    async def send_alert(self, signal: dict):
        """
        Sends a rich embed to Discord.
        """
        if not self.webhook_url:
            logger.warning("No Discord Webhook URL provided.")
            return

        embed = {
            "title": f"🚀 PUMP SIGNAL: {signal['ticker']}",
            "description": f"**Confidence:** {signal['confidence']:.2f}\n**Sentiment Z:** {signal['sentiment_z']:.2f}\n**Volume Z:** {signal['volume_z']:.2f}",
            "color": 5763719, # Green
            "fields": [
                {"name": "Action", "value": "Check Charts", "inline": True}
            ],
            "footer": {"text": "Ticker Agent v2"}
        }
        
        payload = {"embeds": [embed]}
        
        try:
            await self.client.post(self.webhook_url, json=payload)
            logger.info(f"Alert sent for {signal['ticker']}")
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")

    async def close(self):
        await self.client.aclose()

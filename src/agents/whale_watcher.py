
from duckduckgo_search import DDGS
from loguru import logger
from src.data.market_makers import MM_KEYWORDS

class WhaleWatcher:
    def __init__(self):
        self.ddgs = DDGS()
        
    async def check_whale_activity(self, ticker: str) -> str:
        """
        Checks for Market Maker / Whale activity via:
        1. Web Search (News/Announcements)
        2. (Future) On-Chain Holder Analysis
        """
        ticker_clean = ticker.replace("$", "")
        signals = []
        
        # 1. Search for MM Association
        try:
            for keyword in MM_KEYWORDS:
                query = f"{ticker_clean} {keyword}"
                results = list(self.ddgs.text(query, max_results=2))
                
                if results:
                    # Check if result is recent or relevant
                    # Simplifying: if we find *any* result mentioning the ticker and MM, we flag it.
                    for res in results:
                        title = res.get('title', '').lower()
                        body = res.get('body', '').lower()
                        
                        if ticker_clean.lower() in title or ticker_clean.lower() in body:
                            # It's a hit
                            signals.append(f"Found mention: {res.get('title')}")
                            
        except Exception as e:
            logger.error(f"Whale search failed: {e}")
            
        if signals:
            return "WHALE ALERT: " + " | ".join(signals[:3])
        else:
            return "No obvious whale news."

    def analyze_holders(self, holders_list: list) -> str:
        """
        Checks if any holder in the list is a known MM.
        (Placeholder for when we have real holder data)
        """
        # TODO: Implement matching with MARKET_MAKERS dict
        return "Holder analysis pending API."

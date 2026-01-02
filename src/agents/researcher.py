from typing import Dict, Any
from loguru import logger
import asyncio

# Import Ensemble
try:
    from llm.ensemble import EnsembleAnalyst
except ImportError:
    EnsembleAnalyst = None

class WebResearcher:
    def __init__(self):
        self.ensemble = None
        if EnsembleAnalyst:
            self.ensemble = EnsembleAnalyst()
            
        try:
            from duckduckgo_search import DDGS
            self.ddgs = DDGS()
            self.available = True
        except ImportError:
            logger.warning("duckduckgo_search not installed.")
            self.available = False
            self.ddgs = None
        except Exception as e:
            logger.error(f"Failed to init WebResearcher: {e}")
            self.available = False
            self.ddgs = None

    async def verify_signal(self, ticker: str, technicals: Dict[str, Any] = None) -> Dict[str, any]:
        """
        Searches web and uses LLM Ensemble to verify signal.
        """
        if not self.available or not self.ddgs:
            return {"verified": True, "risk_level": "UNKNOWN", "notes": "Researcher unavailable"}
            
        if not technicals:
            technicals = {"rsi": 50, "macd": 0, "price": 0}

        ticker_clean = ticker.replace("$", "")
        
    async def gather_intel(self, ticker: str) -> str:
        """Just gathers news/search results."""
        if not self.available or not self.ddgs:
            return "No web access."
            
        ticker_clean = ticker.replace("$", "")
        # Gather News
        try:
            query = f"{ticker_clean} token crypto news analysis"
            results = list(self.ddgs.text(query, max_results=4))
            
            news_summary = ""
            for res in results:
                news_summary += f"- {res.get('title')}: {res.get('body')}\n"
                
            return news_summary if news_summary else "No news found."
        except Exception as e:
            return f"Error gathering intel: {e}"

    async def verify_signal(self, ticker: str, technicals: Dict[str, Any] = None) -> Dict[str, any]:
        """
        Searches web and uses LLM Ensemble to verify signal.
        """
        if not self.available or not self.ddgs:
            return {"verified": True, "risk_level": "UNKNOWN", "notes": "Researcher unavailable"}
            
        if not technicals:
            technicals = {"rsi": 50, "macd": 0, "price": 0}

        try:
            # 1. Gather News (Context)
            news_summary = await self.gather_intel(ticker)

            # 2. Ask the Council (LLM Ensemble)
            if self.ensemble and self.ensemble.providers:
                logger.info(f"🤖 Convening Council of Experts for {ticker}...")
                verdict = await self.ensemble.analyze_signal(ticker, technicals, news_summary)
                
                # Decision Threshold
                # If Critic found serious issues, confidence will be low.
                risk_level = "LOW"
                verified = True
                
                if verdict["confidence"] < 40:
                    risk_level = "HIGH"
                    verified = False
                elif verdict["confidence"] < 65:
                    risk_level = "MEDIUM"
                    # We might still verify it but with caution
                    verified = True 
                    
                return {
                    "verified": verified,
                    "risk_level": risk_level,
                    "notes": f"Council Conf: {verdict['confidence']}/100. {verdict['rationale']}",
                    "details": verdict
                }
            
            # Fallback to old keywords if no LLM
            user_risk_keywords = ["scam", "rug", "exploit", "honeypot"]
            for word in user_risk_keywords:
                if word in news_summary.lower():
                     return {"verified": False, "risk_level": "HIGH", "notes": f"Keyword '{word}' found."}
                     
            return {
                "verified": True,
                "risk_level": "LOW", 
                "notes": "No immediate flags (Legacy Search)"
            }
            
        except Exception as e:
            logger.error(f"Research failed for {ticker}: {e}")
            return {"verified": True, "risk_level": "UNKNOWN", "notes": f"Error: {e}"}

if __name__ == "__main__":
    # Test
    async def main():
        r = WebResearcher()
        # Mock tech data
        print(await r.verify_signal("$SOL", {"rsi": 30, "macd": -0.5, "price": 145}))
    asyncio.run(main())

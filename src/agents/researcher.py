
from typing import Any, Dict
from loguru import logger

class WebResearcher:
    def __init__(self):
        try:
            from duckduckgo_search import DDGS
            self.ddgs = DDGS()
            self.available = True
        except ImportError:
            logger.warning("duckduckgo_search not installed. Research capabilities disabled.")
            logger.warning("Install with: pip install duckduckgo-search")
            self.available = False
            self.ddgs = None
        except Exception as e:
            logger.error(f"Failed to init WebResearcher: {e}")
            self.available = False
            self.ddgs = None

    def verify_signal(self, ticker: str) -> Dict[str, Any]:
        """
        Searches web for warnings/FUD about the ticker.
        Returns: { 'verified': bool, 'risk_level': str, 'notes': str }
        """
        if not self.available or not self.ddgs:
            return {"verified": True, "risk_level": "UNKNOWN", "notes": "Researcher unavailable"}
            
        ticker_clean = ticker.replace("$", "")
        
        # 1. Search for "scam" or "rug pull"
        # We limit results to 3 to be fast
        try:
            query = f"{ticker_clean} token crypto scam rug pull"
            results = list(self.ddgs.text(query, max_results=3))
            
            risk_keywords = ["scam", "rug", "exploit", "honeypot", "steal", "drain"]
            found_risks = []
            
            for res in results:
                title = res.get('title', '').lower()
                body = res.get('body', '').lower()
                
                for word in risk_keywords:
                    if word in title: # Title matches are high risk
                        found_risks.append(f"Found warning in title: {res.get('title')}")
            
            if found_risks:
                logger.warning(f"Researcher found RISKS for {ticker}: {found_risks}")
                return {
                    "verified": False,
                    "risk_level": "HIGH",
                    "notes": "; ".join(found_risks[:2])
                }
                
            # 2. Search for generic news
            query_news = f"{ticker_clean} crypto token news"
            news_results = list(self.ddgs.text(query_news, max_results=2))
            
            # If nothing found at all, might be too new/obscure (Risk)
            if not results and not news_results:
                 return {
                    "verified": True, # Technically verified as "no bad news", but cautious
                    "risk_level": "MEDIUM", 
                    "notes": "No web presence found"
                }
                
            return {
                "verified": True,
                "risk_level": "LOW",
                "notes": "No immediate red flags found on web"
            }
            
        except Exception as e:
            logger.error(f"Research failed for {ticker}: {e}")
            return {"verified": True, "risk_level": "UNKNOWN", "notes": f"Error: {e}"}

if __name__ == "__main__":
    # Test
    r = WebResearcher()
    print(r.verify_signal("$SOL"))

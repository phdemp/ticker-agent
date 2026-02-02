
import asyncio
import os
import sys
import json
import socket
import logging
from datetime import datetime
from dotenv import load_dotenv

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from loguru import logger
from db import DB_PATH, get_db_connection
from scrapers.coinmarketcap import CoinMarketCapScraper
from scrapers.dexscreener import DexScreenerScraper
from scrapers.cointelegraph import CointelegraphScraper
from ml.sentiment import SentimentAnalyzer
from ml.correlator import SignalCorrelator
from trader.strategy_manager import StrategyManager
from trader.paper import PaperTrader

# Configure separate logger for the tester
logger.add("logs/system_health_{time}.log", rotation="1 day")

class TesterBot:
    def __init__(self):
        load_dotenv()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "status": "pass",
            "checks": []
        }
        self.errors = []

    def log_check(self, name: str, status: bool, message: str = ""):
        """Helper to log check results."""
        icon = "✅" if status else "❌"
        self.results["checks"].append({
            "name": name,
            "status": "pass" if status else "fail",
            "message": message
        })
        if not status:
            self.results["status"] = "fail"
            self.errors.append(f"{name}: {message}")
            logger.error(f"{icon} {name} FAILED: {message}")
        else:
            logger.info(f"{icon} {name}: {message}")

    async def check_connectivity(self):
        """Check basic internet connectivity."""
        logger.info("--- 1. Connectivity Checks ---")
        try:
            # Check DNS
            socket.gethostbyname("google.com")
            self.log_check("DNS Resolution", True, "Successfully resolved google.com")
        except Exception as e:
            self.log_check("DNS Resolution", False, str(e))

        try:
            # Check HTTPS
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://www.google.com", timeout=5.0)
                if resp.status_code == 200:
                    self.log_check("Internet Access", True, "HTTPS GET successful")
                else:
                    self.log_check("Internet Access", False, f"Status Code: {resp.status_code}")
        except Exception as e:
            self.log_check("Internet Access", False, str(e))

    def check_database(self):
        """Check DuckDB and critical tables."""
        logger.info("--- 2. Database Checks ---")
        try:
            if not os.path.exists(DB_PATH):
                self.log_check("DB File Exists", False, f"Missing {DB_PATH}")
                return
            
            self.log_check("DB File Exists", True, "Found database file")
            
            conn = get_db_connection()
            # Check trades table
            try:
                count = conn.execute("SELECT count(*) FROM trades").fetchone()[0]
                self.log_check("Table: trades", True, f"Accessible, Rows: {count}")
            except Exception as e:
                 self.log_check("Table: trades", False, str(e))

            # Check strategies table
            try:
                count = conn.execute("SELECT count(*) FROM strategies").fetchone()[0]
                self.log_check("Table: strategies", True, f"Accessible, Rows: {count}")
            except Exception as e:
                 self.log_check("Table: strategies", False, str(e))
                 
            conn.close()

        except Exception as e:
             self.log_check("Database Connection", False, str(e))

    async def check_market_data(self):
        """Check CoinMarketCap and DexScreener."""
        logger.info("--- 3. Market Data Checks ---")
        
        # CoinMarketCap
        try:
            cmc = CoinMarketCapScraper()
            if not cmc.api_key:
                self.log_check("CMC API Key", False, "Missing COINMARKETCAP_API_KEY")
            else:
                quotes = await cmc.get_quotes(["$BTC"])
                if quotes and "$BTC" in quotes:
                    price = quotes["$BTC"]["price"]
                    self.log_check("CoinMarketCap Quote", True, f"BTC Price: ${price:,.2f}")
                else:
                    self.log_check("CoinMarketCap Quote", False, "Returned empty data")
        except Exception as e:
            self.log_check("CoinMarketCap Scraper", False, str(e))

        # DexScreener
        try:
            dex = DexScreenerScraper()
            data = await dex.scrape("BTC", limit=1)
            if data:
                price = data[0].get("price", "N/A")
                self.log_check("DexScreener Scrape", True, f"BTC Pair Found: ${price}")
            else:
                self.log_check("DexScreener Scrape", False, "No data returned for BTC")
        except Exception as e:
            self.log_check("DexScreener Scraper", False, str(e))

    async def check_intelligence(self):
        """Check News, Sentiment, and ML."""
        logger.info("--- 4. Intelligence Checks ---")
        
        # News
        try:
            news_scraper = CointelegraphScraper()
            articles = await news_scraper.scrape(limit=1)
            if articles:
                title = articles[0]["metadata"]["title"]
                self.log_check("Cointelegraph News", True, f"Fetched: {title[:30]}...")
            else:
                self.log_check("Cointelegraph News", False, "No articles found")
        except Exception as e:
            self.log_check("Cointelegraph Scraper", False, str(e))

        # Sentiment & Correlation
        try:
            analyzer = SentimentAnalyzer()
            score = analyzer.analyze("Bitcoin is creating wealth for everyone!")
            self.log_check("Sentiment Analysis", True, f"Positive Test Score: {score}")

            correlator = SignalCorrelator()
            self.log_check("Signal Correlator", True, "Initialized Successfully")
        except Exception as e:
            self.log_check("ML Components", False, str(e))

    async def check_agents(self):
        """Check Strategy Manager and Bot Connectivity."""
        logger.info("--- 5. Agent Checks ---")
        try:
            manager = StrategyManager()
            active_bots = len(manager.bots)
            self.log_check("Strategy Manager", True, f"Active Bots: {active_bots}")
            
            if "Gemini_Trend" in manager.bots:
                bot = manager.bots["Gemini_Trend"]
                # Simple ping
                try:
                    resp = await bot.generate("Say 'Online'", system_instruction="You are a ping bot.")
                    if resp:
                        self.log_check("Bot: Gemini_Trend", True, f"Response: {resp.strip()}")
                    else:
                        self.log_check("Bot: Gemini_Trend", False, "No response")
                except Exception as e:
                    self.log_check("Bot: Gemini_Trend", False, str(e))
            else:
                 self.log_check("Bot: Gemini_Trend", False, "Not loaded (Missing Key?)")
                 
        except Exception as e:
            self.log_check("Strategy Manager", False, str(e))

    def check_trading(self):
        """Check Paper Trader and Portfolio."""
        logger.info("--- 6. Trading Checks ---")
        try:
            trader = PaperTrader()
            bal = trader.get_balance()
            self.log_check("Portfolio Balance", True, f"${bal:,.2f}")
            
            # Dry Run Trade
            ticker = "TEST_HEALTH"
            success = trader.open_trade(ticker, 100.0, 10.0, 99, "Health Check", "TesterBot")
            
            if success:
                self.log_check("Order Execution", True, "Trade Opened Successfully")
                
                # CLEANUP
                # We need to manually delete this test trade to not pollute the DB
                try:
                    conn = get_db_connection()
                    conn.execute(f"DELETE FROM trades WHERE ticker='{ticker}' AND bot_id='TesterBot'")
                    conn.close()
                    self.log_check("Cleanup", True, "Test trade deleted from DB")
                except Exception as e:
                    self.log_check("Cleanup", False, f"Failed to delete test trade: {e}")
            else:
                self.log_check("Order Execution", False, "Failed to open trade")
                
        except Exception as e:
            self.log_check("Paper Trader", False, str(e))

    async def run_all(self):
        logger.info("🤖 Tester Bot: Starting System Health Check...")
        
        await self.check_connectivity()
        self.check_database()
        await self.check_market_data()
        await self.check_intelligence()
        await self.check_agents()
        self.check_trading()
        
        # summary
        print("\n" + "="*40)
        print(f"SYSTEM STATUS: {self.results['status'].upper()}")
        print("="*40)
        for check in self.results["checks"]:
            icon = "✅" if check["status"] == "pass" else "❌"
            print(f"{icon} {check['name']:<20} | {check['message']}")
        
        # Save Report
        os.makedirs("logs", exist_ok=True)
        with open("logs/latest_health.json", "w") as f:
            json.dump(self.results, f, indent=2)

if __name__ == "__main__":
    bot = TesterBot()
    asyncio.run(bot.run_all())

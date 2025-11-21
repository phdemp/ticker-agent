import asyncio
import os
from dotenv import load_dotenv
from loguru import logger

from db import init_db, get_db_connection
from scrapers.nitter import NitterScraper
from scrapers.dexscreener import DexScreenerScraper
from ml.sentiment import SentimentAnalyzer
from ml.correlator import SignalCorrelator
from notifications import DiscordNotifier
from safety.rugcheck import RugCheck
from dashboard import generate_dashboard

load_dotenv()

# Configuration
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
WATCHLIST = ["$SOL", "$BTC", "$ETH", "$PEPE", "$WIF"] # Example watchlist

async def main():
    logger.info("Starting Ticker Agent v2...")
    init_db()
    
    # Initialize components
    nitter = NitterScraper()
    dex = DexScreenerScraper()
    sentiment_analyzer = SentimentAnalyzer()
    correlator = SignalCorrelator()
    notifier = DiscordNotifier(DISCORD_WEBHOOK)
    rug_checker = RugCheck()
    
    try:
        for ticker in WATCHLIST:
            logger.info(f"Analyzing {ticker}...")
            
            # 1. Scrape Social (Nitter)
            tweets = await nitter.scrape(ticker, limit=20)
            avg_sentiment = 0.0
            if tweets:
                scores = [sentiment_analyzer.analyze(t['content']) for t in tweets]
                avg_sentiment = sum(scores) / len(scores)
                logger.info(f"{ticker} Sentiment: {avg_sentiment:.2f} ({len(tweets)} tweets)")
            
            # 2. Scrape Market (DexScreener)
            # Remove $ for DexScreener search
            clean_ticker = ticker.replace("$", "")
            market_data = await dex.scrape(clean_ticker, limit=1)
            current_volume = 0.0
            token_address = ""
            
            if market_data:
                data = market_data[0]
                current_volume = float(data['metadata'].get('txns', {}).get('h24', 0) or 0)
                token_address = data['metadata'].get('tokenAddress')
                logger.info(f"{ticker} 24h Txns: {current_volume}")

            # 3. Safety Check (if address found)
            is_safe = True
            if token_address:
                safety_report = await rug_checker.check_token(token_address)
                if not safety_report['is_safe']:
                    logger.warning(f"⚠️ {ticker} flagged as UNSAFE by RugCheck!")
                    is_safe = False
            
            # 4. Correlate & Alert
            # Note: In a real run, we'd fetch history from DB. 
            # For this demo, we use dummy history to simulate Z-scores.
            dummy_sent_history = [0.1, 0.2, 0.0, 0.1, 0.05]
            dummy_vol_history = [100, 120, 90, 110, 100]
            
            if is_safe:
                signal = correlator.correlate(
                    ticker, 
                    dummy_sent_history, 
                    dummy_vol_history, 
                    avg_sentiment, 
                    current_volume
                )
                
                if signal['is_pump']:
                    await notifier.send_alert(signal)
            
    except Exception as e:
        logger.error(f"Main loop error: {e}")
    finally:
        await nitter.close()
        await dex.close()
        await notifier.close()
        await rug_checker.close()
        generate_dashboard()
        logger.info("Run complete.")

if __name__ == "__main__":
    asyncio.run(main())

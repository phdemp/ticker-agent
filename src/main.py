import asyncio
import os
from dotenv import load_dotenv
from loguru import logger

from db import init_db, get_db_connection
from scrapers.nitter import NitterScraper
from scrapers.dexscreener import DexScreenerScraper
from scrapers.defillama import DeFiLlamaScraper
from scrapers.cointelegraph import CointelegraphScraper
from scrapers.artemis import ArtemisScraper
from ml.sentiment import SentimentAnalyzer
from ml.correlator import SignalCorrelator
from notifications import DiscordNotifier
from safety.rugcheck import RugCheck
from dashboard import generate_dashboard

load_dotenv()

# Configuration
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
ARTEMIS_API_KEY = os.getenv("ARTEMIS_API_KEY")

# Expanded Watchlist for Multi-Strategy
WATCHLIST = [
    "$SOL", "$BTC", "$ETH", # Safe
    "$JUP", "$PYTH", "$WIF", "$BONK", # Mid
    "$POPCAT", "$MYRO", "$WEN", "$DUKO", "$BOME", "$SLERF" # Degen/Risky
]

async def main():
    logger.info("Starting Ticker Agent v2...")
    init_db()
    
    # Initialize components
    nitter = NitterScraper()
    dex = DexScreenerScraper()
    defillama = DeFiLlamaScraper()
    cointelegraph = CointelegraphScraper()
    artemis = ArtemisScraper()
    sentiment_analyzer = SentimentAnalyzer()
    correlator = SignalCorrelator()
    notifier = DiscordNotifier(DISCORD_WEBHOOK)
    rug_checker = RugCheck()
    
    analyzed_tokens = []

        # 0.1 Cointelegraph News
        logger.info("Fetching Cointelegraph News...")
        news = await cointelegraph.scrape(limit=5)
        global_sentiment = 0
        if news:
            scores = [sentiment_analyzer.analyze(n['content']) for n in news]
            global_sentiment = sum(scores) / len(scores)
            logger.info(f"Global News Sentiment: {global_sentiment:.2f} (based on {len(news)} articles)")
            for article in news:
                logger.info(f"News: {article['metadata']['title']}")
                
                # Extract tickers from news (Simple heuristic)
                # Look for words starting with $ or all-caps words that are 3-5 chars long
                words = article['metadata']['title'].split()
                for word in words:
                    clean_word = word.strip(".,!?()[]")
                    if clean_word.startswith("$") and len(clean_word) > 1:
                        dynamic_watchlist.add(clean_word.upper())
                        logger.info(f"Found ticker in news: {clean_word}")
                    elif clean_word.isupper() and 3 <= len(clean_word) <= 5 and clean_word not in ["THE", "AND", "FOR", "WHY", "HOW", "NEW", "ETF", "SEC", "CEO"]:
                        # Heuristic: assume it's a ticker if all caps and short, excluding common words
                        # This is risky but fits "trending from sentiment" request
                        ticker = f"${clean_word}"
                        dynamic_watchlist.add(ticker)
                        logger.info(f"Found potential ticker in news: {ticker}")

        # 0.2 Artemis Stablecoin Flows
        logger.info("Fetching Artemis Stablecoin Flows...")
        # Check supported assets (test free endpoint)
        assets = await artemis.get_assets()
        if assets:
            logger.info(f"Artemis: Found {len(assets)} supported assets (Free Endpoint Working!)")
        
        # Example: Check Solana flows
        sol_flows = await artemis.get_stablecoin_flows("solana")
        if sol_flows:
            logger.info(f"Solana Stablecoin Flows: {sol_flows}")

        # 0.3 Dynamic Token Discovery
        logger.info("Fetching trending tokens (Boosts)...")
        boosts = await dex.get_token_boosts()
        # dynamic_watchlist is already initialized before news block? No, wait.
        # We need to initialize dynamic_watchlist BEFORE news block or ensure it's available.
        # Let's fix the order in the full file context or just initialize it here if not exists.
        # Actually, looking at previous code, dynamic_watchlist was initialized later.
        # I should move initialization UP.
        
        # RE-WRITING BLOCK TO HANDLE ORDER CORRECTLY
        
    try:
        # Initialize dynamic watchlist with static list
        dynamic_watchlist = set(WATCHLIST)

        # 0. Scrape Global DeFi Stats
        logger.info("Fetching Global DeFi Stats...")
        defi_stats = await defillama.scrape()
        if defi_stats:
            logger.info(f"Global TVL: ${defi_stats[0]['tvl']:,.2f}")

        # 0.1 Cointelegraph News
        logger.info("Fetching Cointelegraph News...")
        news = await cointelegraph.scrape(limit=5)
        global_sentiment = 0
        if news:
            scores = [sentiment_analyzer.analyze(n['content']) for n in news]
            global_sentiment = sum(scores) / len(scores)
            logger.info(f"Global News Sentiment: {global_sentiment:.2f} (based on {len(news)} articles)")
            for article in news:
                logger.info(f"News: {article['metadata']['title']}")
                
                # Extract tickers from news
                words = article['metadata']['title'].split()
                for word in words:
                    clean_word = word.strip(".,!?()[]")
                    if clean_word.startswith("$") and len(clean_word) > 1:
                        dynamic_watchlist.add(clean_word.upper())
                        logger.info(f"Found ticker in news: {clean_word}")
                    elif clean_word.isupper() and 3 <= len(clean_word) <= 5 and clean_word not in ["THE", "AND", "FOR", "WHY", "HOW", "NEW", "ETF", "SEC", "CEO", "USD", "ATH", "BTC", "ETH"]:
                        # Add $BTC and $ETH are already in safe list, but good to exclude common acronyms
                        ticker = f"${clean_word}"
                        dynamic_watchlist.add(ticker)
                        logger.info(f"Found potential ticker in news: {ticker}")

        # 0.2 Artemis Stablecoin Flows
        logger.info("Fetching Artemis Stablecoin Flows...")
        assets = await artemis.get_assets()
        if assets:
            logger.info(f"Artemis: Found {len(assets)} supported assets (Free Endpoint Working!)")
        
        sol_flows = await artemis.get_stablecoin_flows("solana")
        if sol_flows:
            logger.info(f"Solana Stablecoin Flows: {sol_flows}")

        # 0.3 Dynamic Token Discovery (DexScreener Boosts)
        logger.info("Fetching trending tokens (Boosts)...")
        boosts = await dex.get_token_boosts()
        
        # Resolve top 10 boosts to symbols
        for boost in boosts[:10]:
            try:
                address = boost.get("tokenAddress")
                if address:
                    pair_data = await dex.scrape(address, limit=1)
                    if pair_data:
                        symbol = pair_data[0]['metadata'].get('symbol')
                        if symbol:
                            ticker = f"${symbol}"
                            dynamic_watchlist.add(ticker)
                            logger.info(f"Discovered trending token: {ticker}")
            except Exception as e:
                logger.error(f"Failed to resolve boost {boost.get('tokenAddress')}: {e}")

        logger.info(f"Final Watchlist: {dynamic_watchlist}")

        for ticker in dynamic_watchlist:
            # ... (rest of loop is same)
            pass # Placeholder for replace tool context
            
    # ... (rest of file)
    
    finally:
        # ...
        generate_dashboard(
            defi_stats=defi_stats[0] if 'defi_stats' in locals() and defi_stats else None,
            top_picks=top_picks if 'top_picks' in locals() else None,
            news=news if 'news' in locals() else None
        )
        logger.info("Run complete.")

if __name__ == "__main__":
    asyncio.run(main())

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

    try:
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

        # 0.2 Artemis Stablecoin Flows
        logger.info("Fetching Artemis Stablecoin Flows...")
        # Example: Check Solana flows
        sol_flows = await artemis.get_stablecoin_flows("solana")
        if sol_flows:
            logger.info(f"Solana Stablecoin Flows: {sol_flows}")

        # 0.3 Dynamic Token Discovery
        logger.info("Fetching trending tokens (Boosts)...")
        boosts = await dex.get_token_boosts()
        dynamic_watchlist = set(WATCHLIST) # Start with static safe list
        
        # Resolve top 10 boosts to symbols
        for boost in boosts[:10]:
            try:
                # We need to fetch pair data to get the symbol
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
            logger.info(f"Analyzing {ticker}...")
            token_data = {
                "ticker": ticker,
                "price": 0.0,
                "volume": 0.0,
                "sentiment": 0.0,
                "fdv": 0.0,
                "is_safe": True,
                "risk_score": 0,
                "signal": None
            }
            
            # 1. Scrape Social (Nitter)
            tweets = await nitter.scrape(ticker, limit=20)
            if tweets:
                scores = [sentiment_analyzer.analyze(t['content']) for t in tweets]
                token_data["sentiment"] = sum(scores) / len(scores)
                logger.info(f"{ticker} Sentiment: {token_data['sentiment']:.2f} ({len(tweets)} tweets)")
            
            # 2. Scrape Market (DexScreener)
            clean_ticker = ticker.replace("$", "")
            market_data = await dex.scrape(clean_ticker, limit=1)
            
            token_address = ""
            if market_data:
                data = market_data[0]
                try:
                    price_str = data['content'].split('|')[0].replace('Price:', '').strip()
                    token_data["price"] = float(price_str)
                except:
                    token_data["price"] = 0.0
                    
                token_data["volume"] = float(data['metadata'].get('txns', {}).get('h24', 0) or 0)
                token_data["fdv"] = float(data['metadata'].get('fdv', 0) or 0)
                token_address = data['metadata'].get('tokenAddress')
                logger.info(f"{ticker} Price: ${token_data['price']} | FDV: ${token_data['fdv']:,.0f}")

            # 3. Safety Check (if address found and is Solana)
            if token_address:
                chain_id = data['metadata'].get('chainId')
                if chain_id == 'solana':
                    safety_report = await rug_checker.check_token(token_address)
                    token_data["risk_score"] = safety_report.get('score', 0)
                    if not safety_report.get('is_safe', True):
                        logger.warning(f"⚠️ {ticker} flagged as UNSAFE by RugCheck!")
                        token_data["is_safe"] = False
                else:
                    logger.info(f"Skipping RugCheck for {ticker} (Chain: {chain_id})")
            
            # 4. Correlate & Alert
            # Dummy history for demo
            dummy_sent_history = [0.1, 0.2, 0.0, 0.1, 0.05]
            dummy_vol_history = [100, 120, 90, 110, 100]
            
            if token_data["is_safe"]:
                signal = correlator.correlate(
                    ticker, 
                    dummy_sent_history, 
                    dummy_vol_history, 
                    token_data["sentiment"], 
                    token_data["volume"],
                    token_data["price"]
                )
                token_data["signal"] = signal
                
                if signal['is_pump']:
                    await notifier.send_alert(signal)
            
            analyzed_tokens.append(token_data)

        # 5. Multi-Strategy Selection
        logger.info("Selecting top picks...")
        
        # Strategy 1: Safe (High FDV > 1B)
        # Sort by Sentiment (desc), then Volume (desc)
        safe_candidates = [t for t in analyzed_tokens if t["fdv"] > 1_000_000_000]
        safe_pick = sorted(safe_candidates, key=lambda x: (x["sentiment"], x["volume"]), reverse=True)[0] if safe_candidates else None
        
        # Strategy 2: Mid (100M < FDV < 1B)
        mid_candidates = [t for t in analyzed_tokens if 100_000_000 <= t["fdv"] <= 1_000_000_000]
        mid_pick = sorted(mid_candidates, key=lambda x: (x["sentiment"], x["volume"]), reverse=True)[0] if mid_candidates else None
        
        # Strategy 3: Degen (FDV < 100M, Must be Safe)
        # Sort by Volume (desc), then Sentiment (desc)
        degen_candidates = [t for t in analyzed_tokens if t["fdv"] < 100_000_000 and t["is_safe"]]
        degen_pick = sorted(degen_candidates, key=lambda x: (x["volume"], x["sentiment"]), reverse=True)[0] if degen_candidates else None
        
        top_picks = {
            "safe": {**safe_pick, "entry": safe_pick["price"], "target": safe_pick["price"] * 1.10, "stop": safe_pick["price"] * 0.95} if safe_pick else None,
            "mid": {**mid_pick, "entry": mid_pick["price"], "target": mid_pick["price"] * 1.20, "stop": mid_pick["price"] * 0.90} if mid_pick else None,
            "degen": {**degen_pick, "entry": degen_pick["price"], "target": degen_pick["price"] * 1.50, "stop": degen_pick["price"] * 0.80} if degen_pick else None
        }
        
        logger.info(f"Top Picks: Safe={safe_pick['ticker'] if safe_pick else 'None'}, Mid={mid_pick['ticker'] if mid_pick else 'None'}, Degen={degen_pick['ticker'] if degen_pick else 'None'}")

    except Exception as e:
        logger.error(f"Main loop error: {e}")
        top_picks = {"safe": None, "mid": None, "degen": None} # Fallback
    finally:
        await nitter.close()
        await dex.close()
        await defillama.close()
        await cointelegraph.close()
        await artemis.close()
        await notifier.close()
        await rug_checker.close()
        
        generate_dashboard(
            defi_stats=defi_stats[0] if 'defi_stats' in locals() and defi_stats else None,
            top_picks=top_picks if 'top_picks' in locals() else None
        )
        logger.info("Run complete.")

if __name__ == "__main__":
    asyncio.run(main())

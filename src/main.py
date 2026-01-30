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
from scrapers.coinmarketcap import CoinMarketCapScraper
from ml.sentiment import SentimentAnalyzer
from ml.correlator import SignalCorrelator
from notifications import DiscordNotifier
from safety.rugcheck import RugCheck
from dashboard import generate_dashboard
from agents.researcher import WebResearcher
from trader.paper import PaperTrader
from trader.strategy_manager import StrategyManager
from agents.whale_watcher import WhaleWatcher

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
    cmc = CoinMarketCapScraper()
    sentiment_analyzer = SentimentAnalyzer()
    correlator = SignalCorrelator()
    notifier = DiscordNotifier(DISCORD_WEBHOOK)
    rug_checker = RugCheck()
    
    # New Agents
    researcher = WebResearcher()
    trader = PaperTrader()
    strategy_manager = StrategyManager()
    whale_watcher = WhaleWatcher()
    
    analyzed_tokens = []


        
    try:
        # Initialize dynamic watchlist with static list
        dynamic_watchlist = set(WATCHLIST)

        # 0. Scrape Global DeFi Stats
        logger.info("Fetching Global DeFi Stats & Stablecoin Flows...")
        try:
             stablecoin_chains = await defillama.get_stablecoin_chains()
             logger.info(f"Fetched stablecoin data for {len(stablecoin_chains)} chains.")
        except Exception as e:
             logger.error(f"Failed to fetch stablecoin stats: {e}")
             stablecoin_chains = []

        defi_stats = await defillama.scrape()
        if defi_stats:
            logger.info(f"Global TVL: ${defi_stats[0]['tvl']:,.2f}")

        # 0.5 Fetch Top Tokens from CoinMarketCap (Primary Source)
        logger.info("Fetching top tokens from CoinMarketCap...")
        cmc_tokens = await cmc.get_top_tokens(limit=100)
        
        # Initialize dynamic watchlist with CMC tokens + Static list
        # We prioritize CMC tokens.
        dynamic_watchlist = set(cmc_tokens) 
        if not dynamic_watchlist:
            logger.warning("CMC fetch failed/empty. Falling back to static watchlist.")
            dynamic_watchlist = set(WATCHLIST)
        else:
             logger.info(f"Initialized Watchlist with {len(dynamic_watchlist)} tokens from CMC.")
             # Add static safe list just in case they dropped out of top 100 but we still want to track them
             for t in ["$BTC", "$ETH", "$SOL"]:
                 dynamic_watchlist.add(t)

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

        # Batch fetch quotes from CMC for price accuracy
        cmc_quotes = await cmc.get_quotes(list(dynamic_watchlist))
        logger.info(f"Fetched {len(cmc_quotes)} price anchors from CoinMarketCap.")

        for ticker in dynamic_watchlist:
            try:
                # 1. Get Price Anchor from CMC (Source of Truth)
                cmc_data = cmc_quotes.get(ticker)
                
                # 2. Get DexScreener Data for Technicals & Long-tail tickers
                search_query = ticker.lstrip("$")
                pair_data = await dex.scrape(search_query, limit=1)
                
                if not pair_data and not cmc_data:
                    logger.warning(f"No data found for {ticker}")
                    continue
                
                pair = pair_data[0] if pair_data else {}
                
                # If we have CMC data, use it for price. Otherwise, fallback to Dex.
                if cmc_data:
                    current_price = cmc_data['price']
                    current_volume = cmc_data['volume_24h']
                else:
                    current_price = float(pair.get("price", 0) or 0)
                    current_volume = pair.get("volume_profile", {}).get("buys", 0) + pair.get("volume_profile", {}).get("sells", 0)
                
                # 2. Get Sentiment (Mocking history for now as we don't have a DB yet)
                # In prod, fetch from DB
                mock_history = [0.1, 0.2, 0.1, 0.3, 0.2] 
                mock_vol_history = [1000, 1500, 1200, 1800, 2000]
                
                # Mock Price History for Indicators (until we have real historical data)
                # Creating a synthetic trend based on current price to allow indicators to calculate
                p = current_price
                mock_price_history = [p*0.9, p*0.92, p*0.95, p*0.94, p*0.96, p*0.98, p*0.97, p*0.99, p*1.0, p*1.01, p*1.0, p*1.02, p, p]

                # 3. Correlate
                # Use global sentiment as proxy for current sentiment for now
                current_sentiment = global_sentiment
                
                # Extract chain info for ML boosting
                chain_slug = pair.get("metadata", {}).get("chainId", "")

                signal = correlator.correlate(
                    ticker=ticker,
                    sentiment_history=mock_history,
                    volume_history=mock_vol_history,
                    price_history=mock_price_history,
                    current_sentiment=current_sentiment,
                    current_volume=current_volume,
                    current_price=current_price,
                    chain=chain_slug,
                    chain_flows=stablecoin_chains
                )
                
                # 4. Merge DexScreener Data into Signal
                # Fix for broken icons on major tokens
                logo_url = pair.get("logo")
                if not logo_url:
                    if "BTC" in ticker.upper():
                        logo_url = "https://cryptologos.cc/logos/bitcoin-btc-logo.png"
                    elif "ETH" in ticker.upper():
                        logo_url = "https://cryptologos.cc/logos/ethereum-eth-logo.png"
                    elif "SOL" in ticker.upper():
                        logo_url = "https://cryptologos.cc/logos/solana-sol-logo.png"

                signal.update({
                    "name": pair.get("name"),
                    "logo": logo_url,
                    "price": current_price, # Added price to signal
                    "price_change": pair.get("price_change"),
                    "volume_profile": pair.get("volume_profile"),
                    "liquidity": pair.get("metadata", {}).get("liquidity"),
                    "fdv": pair.get("metadata", {}).get("fdv"),
                    "chain": pair.get("metadata", {}).get("chainId"),
                    "pair_address": pair.get("metadata", {}).get("pairAddress"),
                    "url": pair.get("url")
                })
                
                # --- AGENTIC ACTION: Autonomous Bots ---
                # A. Bot Decision Loop (Strategy Manager)
                # Instead of a single "Check > 80", we let all bots analyze reasonable candidates.
                logger.info(f"Checking {ticker} (Conf: {signal['confidence']}%) for Bot Action...")
                
                if signal["confidence"] > 0: 
                    logger.info(f"Candidate {ticker} passed to Autonomous Bots...")
                    
                    # Gather Intel (News/Context)
                    intel = await researcher.gather_intel(ticker)
                    
                    # Gather Whale Intel
                    whale_intel = await whale_watcher.check_whale_activity(ticker)
                    if "WHALE ALERT" in whale_intel:
                         logger.info(f"🐋 {whale_intel}")
                    
                    # Combine Intel for the Bots
                    full_intel = f"{intel}\n\nWHALE DATA (Market Makers): {whale_intel}"
                    
                    # Get Decisions from all active bots
                    tech_data = {
                        "rsi": signal.get("rsi", 50),
                        "macd": signal.get("macd", {}).get("macd", 0),
                        "price": signal.get("price", 0),
                        "ema": signal.get("ema", 0),
                        "volume_z": signal.get("volume_z", 0)
                    }
                    
                    decisions = await strategy_manager.get_decisions(ticker, tech_data, full_intel)
                    
                    for d in decisions:
                        logger.info(f"Bot {d['bot_id']} says: {d['action']} ({d['confidence']}%) - {d['reason']}")
                        
                        if d['action'] == "BUY" and d['confidence'] >= 65:
                             # Execute Trade
                             success = trader.open_trade(
                                 ticker=ticker,
                                 price=current_price,
                                 amount_usd=1000.0, # Fixed size per bot
                                 confidence=d['confidence'],
                                 notes=f"Bot: {d['bot_id']} | {d['reason']}",
                                 bot_id=d['bot_id'],
                                 algorithm_used=d.get('system_prompt', "")
                             )
                             if success:
                                 logger.info(f"🚀 Bot {d['bot_id']} ape'd into {ticker}!")
                
                analyzed_tokens.append(signal)
                logger.info(f"Analyzed {ticker}: Conf {signal['confidence']}%")
                
            except Exception as e:
                logger.error(f"Error analyzing {ticker}: {e}")

        # --- AGENTIC ACTION: Manage Portfolio ---
        # Update active trades
        try:
             # Create a price map for the trader
             current_prices = {}
             for t in analyzed_tokens:
                 current_prices[t['ticker'].replace("$", "").upper()] = t['price']
             
             trader.check_trades(current_prices)
             
             # Fetch Portfolio for Dashboard
             portfolio_data = {
                 "balance_usd": trader.get_balance("USD"),
                 "active_trades": trader.get_active_trades()
             }
        except Exception as e:
             logger.error(f"Portfolio update failed: {e}")
             portfolio_data = {}

        # Sort signals by confidence
        analyzed_tokens.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Determine Top Picks
        top_picks = {
            "safe": {},
            "mid": {},
            "degen": {}
        }
        
        # Helper to find best token in a list of tickers
        def find_best(tickers):
            candidates = [s for s in analyzed_tokens if s['ticker'] in tickers or s['ticker'].replace('$', '') in tickers]
            if candidates:
                return candidates[0]
            return {}

        # Safe: BTC, ETH, SOL
        top_picks['safe'] = find_best(['$BTC', '$ETH', '$SOL', 'BTC', 'ETH', 'SOL'])
        
        # Mid: JUP, PYTH, WIF, BONK
        top_picks['mid'] = find_best(['$JUP', '$PYTH', '$WIF', '$BONK', 'JUP', 'PYTH', 'WIF', 'BONK'])
        
        # Degen: Anything else with high confidence
        safe_mid_tickers = ['$BTC', '$ETH', '$SOL', 'BTC', 'ETH', 'SOL', '$JUP', '$PYTH', '$WIF', '$BONK', 'JUP', 'PYTH', 'WIF', 'BONK']
        degen_candidates = [s for s in analyzed_tokens if s['ticker'] not in safe_mid_tickers and s['ticker'].replace('$', '') not in safe_mid_tickers]
        
        if degen_candidates:
            top_picks['degen'] = degen_candidates[0]
            
        # --- AGENTIC ACTION: Learning Loop ---
        await strategy_manager.run_learning_loop()
            
    except Exception as e:
        logger.error(f"Main loop error: {e}")
    
    finally:
        # ...
        generate_dashboard(
            defi_stats=defi_stats[0] if 'defi_stats' in locals() and defi_stats else None,
            top_picks=top_picks if 'top_picks' in locals() else None,
            news=news if 'news' in locals() else None,
            signals=analyzed_tokens,
            stablecoin_flows=stablecoin_chains,
            portfolio=portfolio_data if 'portfolio_data' in locals() else None
        )
        logger.info("Run complete.")

if __name__ == "__main__":
    asyncio.run(main())
# Trigger redeploy


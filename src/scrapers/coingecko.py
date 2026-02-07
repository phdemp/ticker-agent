import aiohttp
from loguru import logger
from typing import List, Dict, Optional


class CoinGeckoScraper:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        
    async def get_trending_coins(self) -> List[str]:
        """
        Fetches trending cryptocurrencies from CoinGecko.
        Returns a list of ticker symbols (e.g., ['$BTC', '$ETH']).
        This is a FREE endpoint - no API key required.
        """
        url = f"{self.base_url}/search/trending"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        tokens = []
                        
                        # Extract coins from the trending response
                        coins = data.get('coins', [])
                        for item in coins:
                            # The coin data is nested in an 'item' object
                            coin = item.get('item', {})
                            symbol = coin.get('symbol')
                            if symbol:
                                tokens.append(f"${symbol.upper()}")
                        
                        logger.info(f"Fetched {len(tokens)} trending coins from CoinGecko.")
                        return tokens
                    else:
                        error_msg = await response.text()
                        logger.error(f"CoinGecko API Error {response.status}: {error_msg}")
                        return []
        except Exception as e:
            logger.error(f"Failed to fetch trending from CoinGecko: {e}")
            return []
    
    async def get_trending_details(self) -> List[Dict]:
        """
        Fetches detailed trending data including price, market cap, etc.
        Returns a list of dictionaries with full coin details.
        """
        url = f"{self.base_url}/search/trending"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        trending_coins = []
                        
                        coins = data.get('coins', [])
                        for item in coins:
                            coin = item.get('item', {})
                            coin_data = coin.get('data', {})
                            
                            trending_coins.append({
                                'id': coin.get('id'),
                                'name': coin.get('name'),
                                'symbol': coin.get('symbol', '').upper(),
                                'market_cap_rank': coin.get('market_cap_rank'),
                                'thumb': coin.get('thumb'),
                                'large': coin.get('large'),
                                'score': coin.get('score'),
                                'price': coin_data.get('price'),
                                'price_btc': coin_data.get('price_btc'),
                                'total_volume': coin_data.get('total_volume'),
                                'sparkline': coin_data.get('sparkline')
                            })
                        
                        logger.info(f"Fetched detailed data for {len(trending_coins)} trending coins.")
                        return trending_coins
                    else:
                        error_msg = await response.text()
                        logger.error(f"CoinGecko API Error {response.status}: {error_msg}")
                        return []
        except Exception as e:
            logger.error(f"Failed to fetch trending details from CoinGecko: {e}")
            return []


if __name__ == "__main__":
    # Test script
    import asyncio
    
    async def test():
        scraper = CoinGeckoScraper()
        
        # Test basic trending fetch
        tokens = await scraper.get_trending_coins()
        print(f"Trending Tokens: {tokens}")
        
        # Test detailed trending fetch
        details = await scraper.get_trending_details()
        print(f"\nDetailed Trending Data:")
        for coin in details:
            print(f"  {coin['symbol']}: {coin['name']} (Rank: {coin['market_cap_rank']})")
    
    asyncio.run(test())

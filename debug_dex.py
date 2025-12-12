
import asyncio
import aiohttp
import json

async def test_dex_queries():
    queries = ["$SOL", "SOL", "$BOME", "BOME"]
    async with aiohttp.ClientSession() as session:
        for q in queries:
            url = f"https://api.dexscreener.com/latest/dex/search?q={q}"
            print(f"Testing query: {q}")
            async with session.get(url) as response:
                if response.status_code == 200:
                    data = await response.json()
                    pairs = data.get('pairs', [])
                    print(f"Found {len(pairs)} pairs")
                    if pairs:
                        p = pairs[0]
                        print(f"Top result: {p.get('baseToken', {}).get('symbol')} | Price: {p.get('priceUsd')} | Address: {p.get('pairAddress')}")
                else:
                    print(f"Error {response.status_code}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_dex_queries())

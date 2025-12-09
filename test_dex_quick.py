
import asyncio
import aiohttp
import json

async def test_dex():
    url = "https://api.dexscreener.com/latest/dex/search?q=SOL"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if data.get('pairs'):
                pair = data['pairs'][0]
                print(json.dumps(pair, indent=2))

if __name__ == "__main__":
    asyncio.run(test_dex())

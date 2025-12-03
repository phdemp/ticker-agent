import asyncio
import httpx

async def test_trending():
    url = "https://api.dexscreener.com/token-boosts/top/v1"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            # Print first 3 items to see structure
            for item in data[:3]:
                print(item)

if __name__ == "__main__":
    asyncio.run(test_trending())

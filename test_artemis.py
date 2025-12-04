import asyncio
import httpx

async def test_artemis():
    urls = [
        "https://api.artemis.xyz/asset/list",
        "https://api.artemis.xyz/assets",
        "https://api.artemisanalytics.com/api/v1/assets",
        "https://api.artemis.xyz/data/assets"
    ]
    
    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                print(f"Testing {url}...")
                response = await client.get(url)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    print("Success!")
                    print(response.json()[:2])
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_artemis())

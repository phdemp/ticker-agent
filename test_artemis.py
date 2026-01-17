import asyncio
import httpx

async def test_artemis():
    urls = [
        "https://api.artemis.xyz/asset/list",
        "https://api.artemis.io/asset/list",
        "https://api.artemis.com/asset/list",
        "https://artemis.xyz/api/asset/list",
        "https://api.defillama.com/protocols", # Control test
        "https://google.com"
    ]
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for url in urls:
            try:
                print(f"Testing {url}...")
        # Placeholder to prevent tool error from empty content
# I will wait for results.se = await client.get(url)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    print("Success!")
                    print(response.json()[:2])
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_artemis())

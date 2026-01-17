
import asyncio
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def main():
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        print("❌ CEREBRAS_API_KEY not found in .env")
        return

    print(f"✅ Found Key: {api_key[:4]}...")
    
    print("📋 Fetching available models...")
    models_url = "https://api.cerebras.ai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(models_url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                print("Available Models:")
                for m in data['data']:
                    print(f" - {m['id']}")
            else:
                print(f"❌ Failed to list models: {resp.status_code} {resp.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())

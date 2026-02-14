
import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.append('src')
from scrapers.messari import MessariScraper

async def verify_endpoints():
    load_dotenv()
    api_key = os.getenv("MESSARI_API_KEY")
    if not api_key:
        print("⚠️ WARNING: MESSARI_API_KEY not found in env.")
        return
    
    scraper = MessariScraper()
    print("📊 Testing Messari Integration...")
    
    # 1. List Assets
    print("\n1. Testing get_all_assets(limit=3)...")
    assets = await scraper.get_all_assets(limit=3)
    if assets:
        print(f"✅ Success! Fetched {len(assets)} assets.")
        print(f"   Top Asset: {assets[0].get('name')} ({assets[0].get('symbol')})")
    else:
        print("❌ Failed to fetch assets list.")

    # 2. Asset Details
    print("\n2. Testing get_asset_details(['bitcoin', 'ethereum'])...")
    details = await scraper.get_asset_details(['bitcoin', 'ethereum'])
    if details:
        print(f"✅ Success! Fetched {len(details)} asset details.")
        for asset in details:
            print(f"   - {asset.get('name')}: {asset.get('symbol')}")
    else:
        print("❌ Failed to fetch asset details.")

    # 3. Scrape method
    print("\n3. Testing scrape('bitcoin')...")
    result = await scraper.scrape('bitcoin')
    if result:
        print(f"✅ Success! Fetched data for {result[0].get('name')}")
    else:
        print("❌ Failed to scrape bitcoin.")

if __name__ == "__main__":
    asyncio.run(verify_endpoints())

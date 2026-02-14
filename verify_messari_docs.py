
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MESSARI_API_KEY")

print(f"🔑 Key exists: {bool(API_KEY)}")

headers = {
    "x-messari-api-key": API_KEY,
    "Accept": "application/json"
}

# Endpoints derived from https://docs.messari.io/api-reference/endpoints/metrics/v2/assets/get-v2-assets
targets = [
    # List Assets
    "https://api.messari.io/metrics/v2/assets?limit=5",
    
    # Specific Asset (guessing ID/Slug structure based on docs)
    # Docs say: get-v2-assets-details 
    # Usually it's assets/{assetKey} or similar.
    "https://api.messari.io/metrics/v2/assets/bitcoin",
    "https://api.messari.io/metrics/v2/assets/bitcoin/profile"
]

for url in targets:
    try:
        print(f"\nTarget: {url}")
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            print(f"  ✅ SUCCESS! Len: {len(resp.content)}")
            print(f"  Snippet: {resp.text[:100]}")
        else:
             print(f"  ❌ Fail. Response: {resp.text[:200]}")
    except Exception as e:
        print(f"  ⚠️ Error: {e}")

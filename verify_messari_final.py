
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

# Correct endpoint from docs
targets = [
    # List Assets
    "https://api.messari.io/metrics/v2/assets?limit=3",
    
    # Get Asset Details (with query params)
    "https://api.messari.io/metrics/v2/assets/details?assets=bitcoin",
    "https://api.messari.io/metrics/v2/assets/details?assets=bitcoin,ethereum",
]

for url in targets:
    try:
        print(f"\nTarget: {url}")
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            print(f"  ✅ SUCCESS! Len: {len(resp.content)}")
            data = resp.json()
            if 'data' in data and len(data['data']) > 0:
                first = data['data'][0]
                print(f"  First asset: {first.get('name', 'N/A')}")
        else:
             print(f"  ❌ Fail. Response: {resp.text[:200]}")
    except Exception as e:
        print(f"  ⚠️ Error: {e}")

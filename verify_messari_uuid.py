
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

# Bitcoin ID from previous list response
BTC_ID = "1e31218a-e44e-4285-820c-8282ee222035"

targets = [
    # Try ID-based fetch
    f"https://api.messari.io/metrics/v2/assets/{BTC_ID}",
    f"https://api.messari.io/metrics/v2/assets/{BTC_ID}/profile",
    f"https://api.messari.io/metrics/v2/assets/{BTC_ID}/metrics"
]

for url in targets:
    try:
        print(f"\nTarget: {url}")
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            print(f"  ✅ SUCCESS! Len: {len(resp.content)}")
            print(f"  Snippet: {resp.text[:200]}")
        else:
             print(f"  ❌ Fail. Response: {resp.text[:200]}")
    except Exception as e:
        print(f"  ⚠️ Error: {e}")

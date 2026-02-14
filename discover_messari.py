
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MESSARI_API_KEY")

endpoints = [
    "https://data.messari.io/api/v2/assets",
    "https://api.messari.io/api/v2/assets",
    "https://messari.io/api/v2/assets",
    "https://data.messari.io/api/v1/news"
]

print(f"🔑 Key exists: {bool(API_KEY)}")

headers_variations = [
    {"x-messari-api-key": API_KEY},
    {"Authorization": f"Bearer {API_KEY}"}
]

for url in endpoints:
    print(f"\nTarget: {url}")
    for i, headers in enumerate(headers_variations):
        try:
            print(f"  Attempt {i+1} (Headers: {list(headers.keys())})...")
            resp = requests.get(url, headers=headers, timeout=5)
            print(f"    Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"    ✅ SUCCESS! Data len: {len(resp.content)}")
                print(f"    Snippet: {resp.text[:100]}")
            else:
                print(f"    ❌ Fail. Response: {resp.text[:100]}")
        except Exception as e:
            print(f"    ⚠️ Error: {e}")

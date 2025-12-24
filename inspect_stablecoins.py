
import asyncio
import httpx
import json

async def main():
    url_chains = "https://stablecoins.llama.fi/stablecoinchains"
    url_assets = "https://stablecoins.llama.fi/stablecoins?includePrices=true"
    
    print(f"Fetching {url_chains}...")
    async with httpx.AsyncClient() as client:
        resp = await client.get(url_chains)
        if resp.status_code == 200:
            data = resp.json()
            print("--- Chains Data (First Item) ---")
            if data and len(data) > 0:
                print(json.dumps(data[0], indent=2))
        else:
            print(f"Error fetching chains: {resp.status_code}")

        print("\n\nFetching {url_assets}...")
        resp = await client.get(url_assets)
        if resp.status_code == 200:
            data = resp.json()
            pegged = data.get("peggedAssets", [])
            print("--- Assets Data (First Item keys) ---")
            if pegged:
                print(pegged[0].keys())
                print("--- Assets Chain Distribution (First Item chains) ---")
                # Check for chain breakdown keys
                if "chainCirculating" in pegged[0]:
                     print(json.dumps(pegged[0]["chainCirculating"], indent=2)[:500] + "...")
                elif "chains" in pegged[0]:
                     print(pegged[0]["chains"])
        else:
            print(f"Error fetching assets: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(main())

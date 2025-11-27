import asyncio
import httpx
import json

async def test_defillama():
    async with httpx.AsyncClient() as client:
        # 1. Global TVL
        print("Fetching Global TVL...")
        try:
            resp = await client.get("https://api.llama.fi/v2/chains")
            chains = resp.json()
            total_tvl = sum(c.get("tvl", 0) for c in chains)
            print(f"Total TVL: ${total_tvl:,.2f}")
        except Exception as e:
            print(f"Error fetching TVL: {e}")

        # 2. Top Yields
        print("\nFetching Top Yields...")
        try:
            resp = await client.get("https://yields.llama.fi/pools")
            data = resp.json()
            pools = data.get("data", [])
            # Sort by APY and take top 5 with TVL > 1M
            top_pools = sorted([p for p in pools if p['tvlUsd'] > 1_000_000], key=lambda x: x['apy'], reverse=True)[:5]
            for p in top_pools:
                print(f"{p['project']} ({p['symbol']}): {p['apy']:.2f}% APY | TVL: ${p['tvlUsd']:,.0f}")
        except Exception as e:
            print(f"Error fetching Yields: {e}")

        # 3. Stablecoins
        print("\nFetching Stablecoins...")
        try:
            resp = await client.get("https://stablecoins.llama.fi/stablecoins?includePrices=true")
            data = resp.json()
            pegged = data.get("peggedAssets", [])
            total_mcap = sum(p.get("circulating", {}).get("peggedUSD", 0) or 0 for p in pegged)
            print(f"Total Stablecoin Mcap: ${total_mcap:,.2f}")
        except Exception as e:
            print(f"Error fetching Stablecoins: {e}")

if __name__ == "__main__":
    asyncio.run(test_defillama())

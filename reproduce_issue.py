
import asyncio
import httpx
import feedparser
from pprint import pprint

async def fetch_rss():
    url = "https://cointelegraph.com/rss"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            print(f"Entries found: {len(feed.entries)}")
            for i, entry in enumerate(feed.entries[:5]):
                print(f"\n--- Entry {i} ---")
                print(f"Title: {entry.title}")
                print(f"Media Content: {entry.get('media_content')}")
                print(f"Enclosures: {entry.get('enclosures')}")
                
                # Logic from scraper
                image_url = None
                if 'media_content' in entry:
                    image_url = entry.media_content[0].get('url')
                elif 'enclosures' in entry:
                    image_url = entry.enclosures[0].get('href')
                print(f"Extracted Image URL: {image_url}")
                
                # Check description for img tags
                if '<img' in entry.description:
                    print("Image tag found in description")
                else:
                    print("No image tag in description")
        else:
            print(f"Failed to fetch RSS: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(fetch_rss())

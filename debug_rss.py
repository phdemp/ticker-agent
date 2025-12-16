
import feedparser
import requests

def debug_rss():
    url = "https://cointelegraph.com/rss"
    print(f"Fetching {url}...")
    feed = feedparser.parse(url)
    if feed.entries:
        entry = feed.entries[0]
        print(f"Title: {entry.title}")
        print("Keys:", entry.keys())
        if 'media_content' in entry:
            print("Media Content:", entry.media_content)
        if 'links' in entry:
            print("Links:", entry.links)
        if 'enclosures' in entry:
            print("Enclosures:", entry.enclosures)
    else:
        print("No entries found.")

if __name__ == "__main__":
    debug_rss()

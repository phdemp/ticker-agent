
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from scrapers.cointelegraph import CointelegraphScraper

def test():
    scraper = CointelegraphScraper()
    
    bad_url = "https://images.cointelegraph.com/images/528_aHR0cHM6Ly9zMy5jb2ludGVsZWdyYXBoLmNvbS91cGxvYWRzLzIwMjUtMTIvMDE5YjJmNDItOTQzMi03OWIyLThkZDEtN2ZlZjg0OTA4ZTBmLmpwZw==.jpg"
    
    print(f"Testing URL: {bad_url}")
    cleaned = scraper._extract_original_image_url(bad_url)
    print(f"Result: {cleaned}")
    
    if cleaned and "s3.cointelegraph.com" in cleaned:
        print("SUCCESS: Extracted S3 URL")
    else:
        print("FAILURE: Did not extract S3 URL")

if __name__ == "__main__":
    test()

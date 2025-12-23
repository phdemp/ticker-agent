
import sys
import os
import base64
import traceback

# Add src to path
sys.path.append(os.path.abspath("src"))

def test():
    with open("debug_output.txt", "w") as f:
        try:
            from scrapers.cointelegraph import CointelegraphScraper
            f.write("Successfully imported CointelegraphScraper\n")
            
            scraper = CointelegraphScraper()
            
            bad_url = "https://images.cointelegraph.com/images/528_aHR0cHM6Ly9zMy5jb2ludGVsZWdyYXBoLmNvbS91cGxvYWRzLzIwMjUtMTIvMDE5YjJmNDItOTQzMi03OWIyLThkZDEtN2ZlZjg0OTA4ZTBmLmpwZw==.jpg"
            f.write(f"Testing URL: {bad_url}\n")
            
            # Re-implement logic here to trace it step by step if import fails to show internals
            filename = bad_url.split('/')[-1]
            f.write(f"Filename: {filename}\n")
            
            if '.' in filename:
                filename = filename.rsplit('.', 1)[0]
            f.write(f"Filename no ext: {filename}\n")
            
            parts = filename.split('_')
            f.write(f"Parts: {parts}\n")
            
            for i, part in enumerate(parts):
                f.write(f"\nChecking part {i}: {part[:20]}...\n")
                if len(part) < 20: 
                    f.write("Skipping (<20)\n")
                    continue
                
                try:
                    padding = len(part) % 4
                    f.write(f"Length: {len(part)}, Padding needed: {4-padding if padding else 0}\n")
                    if padding:
                        part += '=' * (4 - padding)
                    
                    decoded = None
                    try:
                        decoded = base64.urlsafe_b64decode(part).decode('utf-8')
                        f.write(f"Decoded (urlsafe): {decoded[:50]}...\n")
                    except Exception as e:
                        f.write(f"Failed urlsafe: {e}\n")
                        try:
                            decoded = base64.b64decode(part).decode('utf-8')
                            f.write(f"Decoded (standard): {decoded[:50]}...\n")
                        except Exception as e2:
                            f.write(f"Failed standard: {e2}\n")
                            
                    if decoded and decoded.startswith('http'):
                        f.write(f"SUCCESS MATCH: {decoded}\n")
                except Exception as e:
                     f.write(f"Outer exception: {e}\n")
            
            # Now try the actual class method
            cleaned = scraper._extract_original_image_url(bad_url)
            f.write(f"\nFinal Class Method Result: {cleaned}\n")
            
        except Exception:
            f.write(traceback.format_exc())

if __name__ == "__main__":
    test()

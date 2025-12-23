
import base64
import sys

def test_decode(b64_str):
    print(f"Testing string: {b64_str}")
    
    # 1. Try URL-safe decode
    try:
        # Fix padding locally to be safe
        padding = len(b64_str) % 4
        if padding:
            b64_str += '=' * (4 - padding)
        
        decoded = base64.urlsafe_b64decode(b64_str).decode('utf-8')
        print(f"SUCCESS (urlsafe): {decoded}")
    except Exception as e:
        print(f"FAILED (urlsafe): {e}")

    # 2. Try Standard decode
    try:
        decoded = base64.b64decode(b64_str).decode('utf-8')
        print(f"SUCCESS (standard): {decoded}")
    except Exception as e:
        print(f"FAILED (standard): {e}")

if __name__ == "__main__":
    # String from "Ether ETFs..."
    s = "aHR0cHM6Ly9zMy5jb2ludGVsZWdyYXBoLmNvbS91cGxvYWRzLzIwMjUtMTIvMDE5YjRhMGMtNTg1NS03MGQ2LWI5M2YtNjI0NTI4ZDY1YzVjLmpwZw=="
    test_decode(s)

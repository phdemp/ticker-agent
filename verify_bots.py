import os
import sys
import duckdb
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, 'src')

# Load env
load_dotenv()

print("--- Checking Environment Variables ---")
keys = ["GEMINI_API_KEY", "GROQ_API_KEY", "GITHUB_TOKEN", "CEREBRAS_API_KEY", "HUGGINGFACE_API_TOKEN"]
missing = []
for k in keys:
    val = os.getenv(k)
    status = "✅ SET" if val else "❌ MISSING"
    print(f"{k}: {status}")
    if not val:
        missing.append(k)

if missing:
    print(f"\n❌ Missing Keys: {missing}")
    sys.exit(1)

print("\n--- Initializing Strategy Manager ---")
try:
    from trader.strategy_manager import StrategyManager
    s = StrategyManager()
    print(f"✅ Loaded Bots: {list(s.bots.keys())}")
    
    # Check if all expected bots are present
    expected_bots = ["Gemini_Trend", "Cerebras_Sniper", "Kimi_Narrative", "Phi_Intern", "Llama_Observer"]
    loaded_bots = list(s.bots.keys())
    
    failed_bots = set(expected_bots) - set(loaded_bots)
    if failed_bots:
        print(f"⚠️ Failed to load bots: {failed_bots}")
    else:
        print("🎉 ALL BOTS LOADED SUCCESSFULLY!")
        
except Exception as e:
    print(f"❌ Failed to initialize StrategyManager: {e}")

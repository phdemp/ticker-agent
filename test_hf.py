
import asyncio
import os
from dotenv import load_dotenv
from src.llm.provider import HuggingFaceProvider

load_dotenv()

async def main():
    token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not token:
        print("❌ HUGGINGFACE_API_TOKEN not found in .env")
        return

    print(f"✅ Found Token: {token[:8]}...")
    
    model = "Qwen/Qwen2.5-72B-Instruct"
    print(f"🔄 Testing HF chat/completions with model: {model}")
    
    provider = HuggingFaceProvider(token, model_name=model)
    
    try:
        response = await provider.generate("Say 'Hello World' in Python code only.")
        print(f"✅ Response: {response}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())

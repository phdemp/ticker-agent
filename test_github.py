
import asyncio
import os
from dotenv import load_dotenv
from src.llm.provider import GitHubModelProvider

load_dotenv()

async def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN not found in .env")
        return

    print(f"✅ Found GITHUB_TOKEN: {token[:4]}...{token[-4:]}")
    
    candidate_models = [
        "Phi-3-mini-4k-instruct",
        "Phi-3-mini-128k-instruct",
        "Phi-3.5-mini-instruct",
        "Microsoft/Phi-3-mini-4k-instruct",
        "gpt-4o", # Just to check if token works at all
        "Llama-3.2-90B-Vision-Instruct" 
    ]
    
    for model in candidate_models:
        print(f"\n🔄 Trying model: {model}")
        provider = GitHubModelProvider(token, model_name=model)
        try:
             response = await provider.generate("Hi")
             if "Error" not in response:
                 print(f"✅ WORKING MODEL FOUND: {model}")
                 print(f"Response: {response}")
                 break
             else:
                 print(f"❌ {model} failed: {response}")
        except Exception as e:
            print(f"❌ {model} exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())

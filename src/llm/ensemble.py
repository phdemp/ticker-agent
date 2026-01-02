
import os
import asyncio
from typing import Dict, List
from loguru import logger
from .provider import GeminiProvider, HuggingFaceProvider, GroqProvider, LLMProvider

class EnsembleAnalyst:
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        
        # Load Providers from env
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            self.providers["Analyst"] = GeminiProvider(gemini_key)
            
        hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
        if hf_token:
            # Using Llama 3 as the Critic/Risk Manager
            self.providers["Critic"] = HuggingFaceProvider(hf_token, model_name="meta-llama/Meta-Llama-3-8B-Instruct")

        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            # Using Kimi (via Groq) as the Strategist
            self.providers["Strategist"] = GroqProvider(groq_key, model_name="moonshotai/kimi-k2-instruct-0905")
            
        if not self.providers:
            logger.warning("No LLM Providers available! Ensemble will fail.")

    async def analyze_signal(self, ticker: str, technicals: Dict, news_summary: str) -> Dict[str, any]:
        """
        Conducts a debate between Analyst (Bullish) and Critic (Bearish).
        Returns a consensus confidence score and rationale.
        """
        if not self.providers:
            return {"confidence": 0, "rationale": "No AI models active."}

        # 1. Analyst (Gemini) - The Optimist
        analyst_prompt = f"""
        You are a Crypto Analyst looking for high-growth opportunities. 
        Ticker: {ticker}
        Technicals: RSI={technicals.get('rsi')}, MACD={technicals.get('macd')}, Price=${technicals.get('price')}
        News: {news_summary}
        
        Your Goal: Find reasons to BUY. Be optimistic but logical.
        Output: A short paragraph explaining the BULLISH case.
        """
        
        # 2. Critic (Llama 3) - The Risk Manager
        critic_prompt = f"""
        You are a Risk Manager. Your job is to protect capital.
        Ticker: {ticker}
        Technicals: RSI={technicals.get('rsi')}, MACD={technicals.get('macd')}, Price=${technicals.get('price')}
        News: {news_summary}
        
        Your Goal: Find reasons to AVOID/SELL. Look for overbought signals, divergence, or bad news.
        Output: A short paragraph explaining the BEARISH risks.
        """

        # 3. Strategist (Kimi/Groq) - The Narrative Expert
        strategist_prompt = f"""
        You are a Crypto Narrative Expert.
        Ticker: {ticker}
        News: {news_summary}
        
        Your Goal: Does this token have a strong narrative or community hype? Is it trending? 
        Output: A short paragraph on the NARRATIVE strength.
        """

        # Run in parallel if available
        tasks = []
        # Maintain order for result mapping: Analyst, Critic, Strategist
        # We need to act carefully since dictionary order is not 100% reliable for sync logic if we just iterate keys.
        # Let's map explicit keys.
        
        active_roles = []
        if "Analyst" in self.providers:
            tasks.append(self.providers["Analyst"].generate(analyst_prompt))
            active_roles.append("Analyst")
        if "Critic" in self.providers:
            tasks.append(self.providers["Critic"].generate(critic_prompt))
            active_roles.append("Critic")
        if "Strategist" in self.providers:
            tasks.append(self.providers["Strategist"].generate(strategist_prompt))
            active_roles.append("Strategist")
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect Views
        views = {}
        for i, role in enumerate(active_roles):
            res = results[i]
            views[role] = res if isinstance(res, str) else f"Error: {res}"
        
        
        # 3. Synthesis (Simple Logic for now, or use Analyst to synthesize)
        # Let's ask the Analyst (Gemini) to synthesize the final decision
        if "Analyst" in self.providers and not views["Analyst"].startswith("Error"):
            synthesis_prompt = f"""
            You are the Head Trader. You have heard arguments from your Council.
            
            Bullish Case (Analyst): {views.get('Analyst', 'N/A')}
            Bearish Case (Critic): {views.get('Critic', 'N/A')}
            Narrative Case (Strategist): {views.get('Strategist', 'N/A')}
            
            Task:
            1. Rate the trade from 0 to 100 confidence.
            2. Provide a 1-sentence final decision.
            
            Format:
            CONFIDENCE: <number>
            DECISION: <text>
            """
            final_verdict = await self.providers["Analyst"].generate(synthesis_prompt)
        else:
            final_verdict = "CONFIDENCE: 50\nDECISION: Consensus failed."

        # Parse Verdict
        confidence = 50
        decision = final_verdict
        
        try:
            for line in final_verdict.split('\n'):
                if "CONFIDENCE:" in line:
                    confidence = int(line.split(":")[1].strip())
                if "DECISION:" in line:
                    decision = line.split(":")[1].strip()
        except:
            pass

        return {
            "confidence": confidence,
            "rationale": decision,
            "bull_case": views.get('Analyst', '')[:200] + "...",
            "bear_case": views.get('Critic', '')[:200] + "...",
            "narrative": views.get('Strategist', '')[:200] + "..."
        }

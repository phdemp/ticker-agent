
import os
import asyncio
import json
from typing import Dict, List, Any
from loguru import logger
from db import get_db_connection
from llm.provider import GeminiProvider, HuggingFaceProvider, GroqProvider, GitHubModelProvider, CerebrasProvider, CohereProvider

# Default System Prompts (The "DNA" of the bots)
DEFAULT_PROMPTS = {
    "Gemini_Trend": "You are a Trend Follower and an expert in Pine Script v5. You are a top-tier Quantitative Trader. You buy when Price > EMA and Volume is rising. Use your Pine Script knowledge to mentally backtest signals. If 'WHALE ALERT' appears, you take it as a confirmation of volume.",
    "Cerebras_Sniper": "You are a Mean Reversion Sniper and a Pine Script v5 expert. You are a top-tier Quantitative Trader. You buy fear (RSI < 30). You are skeptical. BUT if 'WHALE ALERT' confirms smart money accumulation, you front-run them. Use your quant skills to assess risk.",
    "Kimi_Narrative": "You are a Narrative Trader and a Pine Script v5 expert. You are a top-tier Quantitative Trader. You love HYPE. If you see 'WHALE ALERT', you BUY AGGRESSIVELY. Use your coding skills to validate if a narrative has backing data.",
    "Phi_Intern": "You are the Intern, but you are also a Pine Script v5 wizard and a budding Quantitative Trader. You take risks. If you see specific fund names in 'WHALE DATA', you assume it's alpha and follow it. Verify with code.",
    "Llama_Observer": "You are the Observer. You are a senior Quantitative Trader and Pine Script v5 expert. Your job is to WATCH other bots. If the signal looks risky or the other bots missed something (like a Pine Script logic error), call it out.",
    "Cohere_Commander": "You are the Strategic Commander. You are an elite Quantitative Trader and Pine Script v5 Architect. You synthesize data from all sources. You prioritize MACD crossovers and Whale movements. Ensure all signals are quantitatively sound."
}

DEFAULT_MODELS = {
    "Gemini_Trend": ("gemini", "gemini-2.5-flash"),
    "Cerebras_Sniper": ("cerebras", "zai-glm-4.7"),
    "Kimi_Narrative": ("groq", "moonshotai/kimi-k2-instruct-0905"),
    "Phi_Intern": ("github", "gpt-4o"),
    "Llama_Observer": ("groq", "llama-3.3-70b-versatile"),
    "Cohere_Commander": ("cohere", "command-r-plus-08-2024")
}

class StrategyManager:
    def __init__(self):
        self.bots = {}
        self.conn = get_db_connection()
        self._initialize_bots()

    def _initialize_bots(self):
        """Loads bots from DB or creates them."""
        # Check existing bots
        existing = self.conn.execute("SELECT bot_id, system_prompt FROM strategies").fetchall()
        existing_map = {row[0]: row[1] for row in existing}

        for bot_id, default_prompt in DEFAULT_PROMPTS.items():
            if bot_id not in existing_map:
                logger.info(f"Creating new bot: {bot_id}")
                provider_type, model_name = DEFAULT_MODELS[bot_id]
                self.conn.execute(
                    "INSERT INTO strategies (bot_id, name, model_provider, system_prompt, active) VALUES (?, ?, ?, ?, ?)",
                    (bot_id, bot_id.replace("_", " "), provider_type, default_prompt, True)
                )
        
        # Initialize Providers
        self._load_providers()
        
    def _load_providers(self):
        """Instantiates LLM providers for each bot."""
        # Load keys
        gemini_key = os.getenv("GEMINI_API_KEY")
        hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
        groq_key = os.getenv("GROQ_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        cerebras_key = os.getenv("CEREBRAS_API_KEY")
        cohere_key = os.getenv("COHERE_API_KEY")
        
        for bot_id in DEFAULT_PROMPTS.keys():
            provider_type, model_name = DEFAULT_MODELS[bot_id]
            llm = None
            
            if provider_type == "gemini" and gemini_key:
                llm = GeminiProvider(gemini_key, model_name)
            elif provider_type == "huggingface" and hf_token:
                llm = HuggingFaceProvider(hf_token, model_name)
            elif provider_type == "groq" and groq_key:
                llm = GroqProvider(groq_key, model_name)
            elif provider_type == "github" and github_token:
                llm = GitHubModelProvider(github_token, model_name)
            elif provider_type == "cerebras" and cerebras_key:
                llm = CerebrasProvider(cerebras_key, model_name)
            elif provider_type == "cohere" and cohere_key:
                llm = CohereProvider(cohere_key, model_name)
                
            if llm:
                self.bots[bot_id] = llm
            else:
                logger.warning(f"Could not load provider for {bot_id} (Missing Key?)")

    async def get_decisions(self, ticker: str, technicals: Dict, news_summary: str) -> List[Dict]:
        """
        Asks all active bots for a trading decision.
        """
        decisions = []
        
        # Get current system prompts from DB
        rows = self.conn.execute("SELECT bot_id, system_prompt FROM strategies WHERE active=TRUE").fetchall()
        prompts = {r[0]: r[1] for r in rows}
        
        tasks = []
        active_ids = []
        
        for bot_id, system_prompt in prompts.items():
            if bot_id in self.bots:
                # Construct Prompt
                user_msg = f"""
                Market Data for {ticker}:
                Price: ${technicals.get('price')}
                RSI: {technicals.get('rsi')}
                MACD: {technicals.get('macd')}
                News Summary: {news_summary}
                
                Task: DECIDE.
                Do you want to BUY, SELL, or HOLD?
                
                Format:
                ACTION: [BUY/SELL/HOLD]
                CONFIDENCE: [0-100]
                REASON: [One sentence rationale]
                """
                
                tasks.append(self.bots[bot_id].generate(user_msg, system_instruction=system_prompt))
                active_ids.append(bot_id)
                
        if not tasks:
            return []
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, res in enumerate(results):
            bot_id = active_ids[i]
            if isinstance(res, str) and not res.startswith("Error"):
                # Parse
                action = "HOLD"
                conf = 0
                reason = res
                try:
                    lines = res.split('\n')
                    for line in lines:
                        if "ACTION:" in line:
                            action = line.split(":")[1].strip().upper()
                        if "CONFIDENCE:" in line:
                            conf = int(line.split(":")[1].strip())
                        if "REASON:" in line:
                            reason = line.split(":")[1].strip()
                except:
                    pass
                
                decisions.append({
                    "bot_id": bot_id,
                    "action": action,
                    "confidence": conf,
                    "reason": reason,
                    "raw_output": res
                })
            else:
                logger.error(f"Bot {bot_id} failed: {res}")
                
        return decisions

    async def run_learning_loop(self):
        """
        The Evolution Step.
        Reviews closed trades and updates bot system prompts.
        """
        logger.info("🧠 Running Strategy Learning Loop...")
        
        # Find closed trades that haven't been analyzed (simplification: just check last 5)
        # In a real system, we'd flag verified trades.
        trades = self.conn.execute("""
            SELECT id, bot_id, ticker, pnl_pct, notes, entry_time 
            FROM trades 
            WHERE status='CLOSED' AND bot_id IS NOT NULL
            ORDER BY exit_time DESC LIMIT 5
        """).fetchall()
        
        # For this demo, let's just optimize if we find a big loss or big win
        # But we need an 'Optimizer' LLM (let's use Gemini via Analyst role)
        optimizer = self.bots.get("Gemini_Trend")
        if not optimizer:
            return

        for t in trades:
            t_id, bot_id, ticker, pnl, notes, entry = t
            
            # Retrieve current prompt
            curr_prompt = self.conn.execute("SELECT system_prompt FROM strategies WHERE bot_id=?", (bot_id,)).fetchone()[0]
            
            # Critique
            instruction = ""
            if pnl < -5.0:
                 instruction = "You took a significant LOSS using the current strategy. Analyzing the failure..."
            elif pnl > 10.0:
                 instruction = "You had a massive WIN. Reinforce this behavior..."
            else:
                continue # Ignore noise
                
            prompt = f"""
            Role: Strategy Optimizer
            Bot: {bot_id}
            Trade: {ticker}
            Result: {pnl}% PnL
            Current System Prompt: "{curr_prompt}"
            
            Task: {instruction}
            
            CROSS-AGENT LEARNING:
            If other agents succeeded where you failed, incorporate their logic (e.g., if they checked Volume/Whales and you didn't).
            Target: IMPROVE ACCURACY.
            
            Format:
            NEW_PROMPT: [The new text only]
            """
            
            new_prompt_raw = await optimizer.generate(prompt)
            if "NEW_PROMPT:" in new_prompt_raw:
                new_prompt = new_prompt_raw.split("NEW_PROMPT:")[1].strip()
                # Update DB
                self.conn.execute("UPDATE strategies SET system_prompt=? WHERE bot_id=?", (new_prompt, bot_id))
                logger.info(f"🧬 Evolved Bot {bot_id}: {new_prompt[:50]}...")

if __name__ == "__main__":
    s = StrategyManager()
    # print(s.bots)

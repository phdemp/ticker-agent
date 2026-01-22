import asyncio
import os
import sys

# Add src to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import get_db_connection
from trader.strategy_manager import DEFAULT_PROMPTS
from loguru import logger

def update_prompts():
    logger.info("Starting prompt update...")
    conn = get_db_connection()
    
    try:
        # Get existing bots
        existing = conn.execute("SELECT bot_id, system_prompt FROM strategies").fetchall()
        existing_ids = [row[0] for row in existing]
        
        updated_count = 0
        
        for bot_id, new_prompt in DEFAULT_PROMPTS.items():
            if bot_id in existing_ids:
                logger.info(f"Updating prompt for {bot_id}...")
                conn.execute(
                    "UPDATE strategies SET system_prompt = ? WHERE bot_id = ?",
                    (new_prompt, bot_id)
                )
                updated_count += 1
            else:
                logger.warning(f"Bot {bot_id} found in defaults but not in DB. Skipping update (StrategyManager will create it).")
                
        conn.commit()
        logger.success(f"Successfully updated {updated_count} bots with new Pine Script & Quant expertise!")
        
    except Exception as e:
        logger.error(f"Failed to update prompts: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_prompts()

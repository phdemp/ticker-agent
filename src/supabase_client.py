
import os
from supabase import create_client, Client
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class SupabaseManager:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.client: Client = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("Supabase client initialized.")
            except Exception as e:
                logger.error(f"Failed to init Supabase client: {e}")
        else:
            logger.warning("Supabase URL or Key missing in .env")

    def sync_trade(self, trade_data: dict):
        """
        Upserts a trade record to Supabase.
        """
        if not self.client:
            return
        
        try:
            # Ensure trade_data keys match Supabase schema
            # Supabase schema: id, ticker, entry_price, amount, entry_time, status, exit_price, exit_time, pnl, pnl_pct, confidence_at_entry, notes, bot_id, algorithm_used
            
            # Helper to map DuckDB keys to Supabase keys if necessary
            # For now, we assume they match or we explicitly map them.
            
            self.client.table("trades").upsert(trade_data).execute()
            logger.info(f"Synced trade {trade_data.get('id')} to Supabase.")
        except Exception as e:
            logger.error(f"Failed to sync trade to Supabase: {e}")

    def sync_strategy(self, strategy_data: dict):
        """
        Upserts a strategy record to Supabase.
        """
        if not self.client:
            return
        
        try:
            self.client.table("strategies").upsert(strategy_data).execute()
            logger.info(f"Synced strategy {strategy_data.get('bot_id')} to Supabase.")
        except Exception as e:
            logger.error(f"Failed to sync strategy to Supabase: {e}")

    def get_historical_trades(self, limit: int = 50):
        """
        Fetches historical trades for learning.
        """
        if not self.client:
            return []
        
        try:
            response = self.client.table("trades").select("*").order("exit_time", desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to fetch historical trades: {e}")
            return []

supabase_sync = SupabaseManager()

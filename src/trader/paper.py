
import duckdb
import datetime
from loguru import logger
from db import DB_PATH

class PaperTrader:
    def __init__(self):
        self.con = duckdb.connect(DB_PATH)
        
    def get_balance(self, asset="USD"):
        res = self.con.execute(f"SELECT balance FROM portfolio WHERE asset='{asset}'").fetchone()
        return res[0] if res else 0.0

    def get_portfolio(self):
        """Returns list of active assets and balances."""
        return self.con.execute("SELECT * FROM portfolio").fetchall()

    def get_active_trades(self):
        col_names = [desc[0] for desc in self.con.description]
        rows = self.con.execute("SELECT * FROM trades WHERE status='OPEN'").fetchall()
        # Convert to dict
        # Assuming schema: id, ticker, entry_price, amount, entry_time, status, exit_price, exit_time, pnl, pnl_pct, confidence, notes
        return rows

    def open_trade(self, ticker: str, price: float, amount_usd: float, confidence: float, notes: str = ""):
        """
        Opens a new paper trade.
        """
        try:
            # Check balance
            usd_bal = self.get_balance("USD")
            if usd_bal < amount_usd:
                logger.warning(f"Insufficient funds ({usd_bal}) to trade {amount_usd} on {ticker}")
                return False

            # Deduct USD
            new_bal = usd_bal - amount_usd
            self.con.execute(f"UPDATE portfolio SET balance={new_bal}, last_updated=current_timestamp WHERE asset='USD'")
            
            # Add Asset (or update existing holding)
            # For simplicity in this v1, we just track the trade row, but we could also track asset tokens in portfolio.
            # Let's just track the trade for PnL purposes.
            
            # Insert Trade
            trade_id = f"{ticker}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            amount_tokens = amount_usd / price
            
            self.con.execute(f"""
                INSERT INTO trades VALUES (
                    '{trade_id}', '{ticker}', {price}, {amount_tokens}, current_timestamp, 
                    'OPEN', 0, NULL, 0, 0, {confidence}, '{notes}'
                )
            """)
            logger.info(f"PAPER TRADE OPENED: {ticker} @ ${price} (${amount_usd})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open trade: {e}")
            return False

    def check_trades(self, current_prices: dict):
        """
        Checks active trades against current prices for Stop Loss / Take Profit.
        Simple logic: TP +15%, SL -10%
        """
        trades = self.con.execute("SELECT * FROM trades WHERE status='OPEN'").fetchall()
        # manual mapping of tuple indices based on db.py schema:
        # 0:id, 1:ticker, 2:entry, 3:amount
        
        for t in trades:
            t_id, ticker, entry, amount = t[0], t[1], t[2], t[3]
            
            # Clean ticker ($SOL -> SOL) for lookup
            clean_ticker = ticker.replace("$", "").upper()
            
            # Find current price
            # We need to map generic tickers to what we have in current_prices (which comes from main.py's analyzed_tokens)
            curr = current_prices.get(clean_ticker) or current_prices.get(ticker)
            
            if not curr:
                continue
                
            curr_price = float(curr)
            pnl_pct = (curr_price - entry) / entry
            
            # TP/SL Logic
            close = False
            reason = ""
            
            if pnl_pct >= 0.15:
                close = True
                reason = "Take Profit (+15%)"
            elif pnl_pct <= -0.10:
                close = True
                reason = "Stop Loss (-10%)"
                
            if close:
                self.close_trade(t_id, curr_price, reason)

    def close_trade(self, trade_id, exit_price, notes=""):
        try:
            # Get trade details
            t = self.con.execute(f"SELECT ticker, amount, entry_price FROM trades WHERE id='{trade_id}'").fetchone()
            if not t: return
            
            ticker, amount, entry = t[0], t[1], t[2]
            usd_returned = amount * exit_price
            pnl = usd_returned - (amount * entry)
            pnl_pct = (exit_price - entry) / entry * 100
            
            # Update Trade
            self.con.execute(f"""
                UPDATE trades SET 
                    status='CLOSED', 
                    exit_price={exit_price}, 
                    exit_time=current_timestamp, 
                    pnl={pnl}, 
                    pnl_pct={pnl_pct},
                    notes=notes || ' - {notes}'
                WHERE id='{trade_id}'
            """)
            
            # Credit USD back
            curr_bal = self.get_balance("USD")
            self.con.execute(f"UPDATE portfolio SET balance={curr_bal + usd_returned} WHERE asset='USD'")
            
            logger.info(f"PAPER TRADE CLOSED: {ticker} | PnL: ${pnl:.2f} ({pnl_pct:.1f}%) | {notes}")
            
        except Exception as e:
            logger.error(f"Failed to close trade: {e}")

    def __del__(self):
        try:
            self.con.close()
        except:
            pass

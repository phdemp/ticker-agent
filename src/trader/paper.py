
import duckdb
import datetime
from loguru import logger
from db import DB_PATH

class PaperTrader:
    def __init__(self):
        self.con = duckdb.connect(DB_PATH)
        
    def get_balance(self, asset="USD"):
        res = self.con.execute("SELECT balance FROM portfolio WHERE asset=?", [asset]).fetchone()
        return res[0] if res else 0.0

    def get_portfolio(self):
        """Returns list of active assets and balances."""
        return self.con.execute("SELECT * FROM portfolio").fetchall()

    def get_active_trades(self):
        rows = self.con.execute("SELECT * FROM trades WHERE status='OPEN'").fetchall()
        # Returns list of tuples with schema: id, ticker, entry_price, amount, entry_time, status, exit_price, exit_time, pnl, pnl_pct, confidence, notes
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
            self.con.execute(
                "UPDATE portfolio SET balance=?, last_updated=current_timestamp WHERE asset='USD'",
                [new_bal]
            )
            
            # Insert Trade
            trade_id = f"{ticker}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            amount_tokens = amount_usd / price
            
            self.con.execute(
                """INSERT INTO trades VALUES (?, ?, ?, ?, current_timestamp, 'OPEN', 0, NULL, 0, 0, ?, ?)""",
                [trade_id, ticker, price, amount_tokens, confidence, notes]
            )
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
            t = self.con.execute(
                "SELECT ticker, amount, entry_price FROM trades WHERE id=?",
                [trade_id]
            ).fetchone()
            if not t: return
            
            ticker, amount, entry = t[0], t[1], t[2]
            usd_returned = amount * exit_price
            pnl = usd_returned - (amount * entry)
            pnl_pct = (exit_price - entry) / entry * 100
            
            # Update Trade
            updated_notes = f"{notes}" if notes else ""
            self.con.execute(
                """UPDATE trades SET 
                    status='CLOSED', 
                    exit_price=?, 
                    exit_time=current_timestamp, 
                    pnl=?, 
                    pnl_pct=?,
                    notes=notes || ' - ' || ?
                WHERE id=?""",
                [exit_price, pnl, pnl_pct, updated_notes, trade_id]
            )
            
            # Credit USD back
            curr_bal = self.get_balance("USD")
            self.con.execute(
                "UPDATE portfolio SET balance=? WHERE asset='USD'",
                [curr_bal + usd_returned]
            )
            
            logger.info(f"PAPER TRADE CLOSED: {ticker} | PnL: ${pnl:.2f} ({pnl_pct:.1f}%) | {notes}")
            
        except Exception as e:
            logger.error(f"Failed to close trade: {e}")

    def __del__(self):
        try:
            self.con.close()
        except:
            pass

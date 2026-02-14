
import duckdb
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))
from db import DB_PATH

def audit():
    con = duckdb.connect(DB_PATH)
    print("--- Trade Distribution ---")
    trades = con.execute("SELECT bot_id, count(*) FROM trades GROUP BY bot_id").fetchall()
    for row in trades:
        print(f"Bot: {row[0]}, Count: {row[1]}")
    
    print("\n--- Bot Configs ---")
    configs = con.execute("SELECT bot_id, model_provider, active FROM strategies").fetchall()
    for row in configs:
        print(f"Bot: {row[0]}, Provider: {row[1]}, Active: {row[2]}")
    
    # Check for errors in recent trade attempts?
    # Actually, let's just see who took the last 10 trades
    print("\n--- Last 10 Trades ---")
    last_trades = con.execute("SELECT id, ticker, bot_id, entry_time FROM trades ORDER BY entry_time DESC LIMIT 10").fetchall()
    for row in last_trades:
        print(row)

if __name__ == "__main__":
    audit()

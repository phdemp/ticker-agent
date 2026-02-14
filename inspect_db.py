import duckdb

def check_db():
    try:
        con = duckdb.connect('ticker.db')
        print("--- Trades Table ---")
        trades = con.execute("SELECT * FROM trades").fetchall()
        print(f"Total Trades: {len(trades)}")
        for t in trades:
            print(t)
            
        print("\n--- Open Trades ---")
        open_trades = con.execute("SELECT * FROM trades WHERE status = 'OPEN'").fetchall()
        print(f"Open Trades: {len(open_trades)}")
        for ot in open_trades:
            print(ot)
            
        print("\n--- Portfolio Status ---")
        portfolio = con.execute("SELECT * FROM portfolio").fetchall()
        for p in portfolio:
            print(p)
            
        con.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()

import duckdb
from loguru import logger

DB_PATH = "ticker.db"

def get_db_connection():
    """Returns a DuckDB connection."""
    return duckdb.connect(DB_PATH)

def init_db():
    """Initializes the database schema."""
    logger.info("Initializing database...")
    con = get_db_connection()
    
    # Tweets/Posts table
    con.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id VARCHAR PRIMARY KEY,
            platform VARCHAR,
            user VARCHAR,
            content VARCHAR,
            timestamp TIMESTAMP,
            cashtags VARCHAR[],
            sentiment DOUBLE,
            url VARCHAR,
            metadata JSON
        )
    """)
    
    # Signals table
    con.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id VARCHAR PRIMARY KEY,
            timestamp TIMESTAMP,
            ticker VARCHAR,
            signal_type VARCHAR,
            confidence DOUBLE,
            sources JSON
        )
    """)
    
    # Whales/Smart Money table
    con.execute("""
        CREATE TABLE IF NOT EXISTS whales (
            tx_hash VARCHAR PRIMARY KEY,
            chain VARCHAR,
            timestamp TIMESTAMP,
            token VARCHAR,
            amount DOUBLE,
            amount_usd DOUBLE,
            sender VARCHAR,
            receiver VARCHAR,
            label VARCHAR
        )
    """)

    # Portfolio table (Paper Trading)
    con.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            asset VARCHAR PRIMARY KEY,
            balance DOUBLE,
            last_updated TIMESTAMP
        )
    """)
    # Initialize USD balance if empty
    res = con.execute("SELECT count(*) FROM portfolio WHERE asset='USD'").fetchone()
    if res[0] == 0:
        con.execute("INSERT INTO portfolio VALUES ('USD', 10000.0, current_timestamp)")

    # Trades table (Paper Trading)
    con.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id VARCHAR PRIMARY KEY,
            ticker VARCHAR,
            entry_price DOUBLE,
            amount DOUBLE, 
            entry_time TIMESTAMP,
            status VARCHAR, -- 'OPEN', 'CLOSED'
            exit_price DOUBLE,
            exit_time TIMESTAMP,
            pnl DOUBLE,
            pnl_pct DOUBLE,
            confidence_at_entry DOUBLE,
            notes VARCHAR,
            bot_id VARCHAR -- ID of the bot that made the trade
        )
    """)
    
    # Attempt to add bot_id column if table existed but column didn't (migration)
    try:
        con.execute("ALTER TABLE trades ADD COLUMN bot_id VARCHAR")
    except:
        pass # Column likely exists

    # Strategies/Bots table
    con.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            bot_id VARCHAR PRIMARY KEY,
            name VARCHAR,
            model_provider VARCHAR,
            system_prompt VARCHAR,
            win_rate DOUBLE DEFAULT 0.0,
            total_pnl DOUBLE DEFAULT 0.0,
            active BOOLEAN DEFAULT TRUE,
            last_updated TIMESTAMP
        )
    """)
    
    con.close()
    logger.info("Database initialized.")

if __name__ == "__main__":
    init_db()

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
    
    con.close()
    logger.info("Database initialized.")

if __name__ == "__main__":
    init_db()

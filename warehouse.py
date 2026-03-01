# warehouse.py
import duckdb

con = duckdb.connect("finance.duckdb")

con.execute("""
    -- Banking Transaktionen (Revolut + C24)
    CREATE TABLE IF NOT EXISTS bank_transactions (
        id VARCHAR PRIMARY KEY,
        source VARCHAR,           -- 'revolut' oder 'c24'
        booking_date DATE,
        amount DECIMAL(12,2),
        currency VARCHAR(3),
        counterpart VARCHAR,
        remittance_info VARCHAR,
        category VARCHAR,
        synced_at TIMESTAMP DEFAULT NOW()
    );

    -- Bitpanda Assets & Trades
    CREATE TABLE IF NOT EXISTS investment_trades (
        id VARCHAR PRIMARY KEY,
        source VARCHAR,           -- 'bitpanda' oder 'zero'
        trade_date DATE,
        type VARCHAR,             -- 'BUY', 'SELL'
        asset_symbol VARCHAR,
        asset_type VARCHAR,       -- 'crypto', 'stock', 'etf', 'metal'
        shares DECIMAL(18,8),
        price_eur DECIMAL(12,4),
        total_eur DECIMAL(12,2),
        synced_at TIMESTAMP DEFAULT NOW()
    );

    -- Bitpanda Portfoliopositionen (Snapshot)
    CREATE TABLE IF NOT EXISTS portfolio_snapshots (
        snapshot_date DATE,
        asset_symbol VARCHAR,
        asset_type VARCHAR,
        quantity DECIMAL(18,8),
        value_eur DECIMAL(12,2),
        PRIMARY KEY (snapshot_date, asset_symbol)
    );

    -- Nettovermögen über Zeit
    CREATE VIEW IF NOT EXISTS net_worth AS
    SELECT 
        snapshot_date,
        SUM(value_eur) as total_value_eur
    FROM portfolio_snapshots
    GROUP BY snapshot_date;
""")
# warehouse.py
import duckdb


def init_database():
    con = duckdb.connect("finance.duckdb")

    con.execute("""
        CREATE TABLE IF NOT EXISTS bank_transactions (
            id VARCHAR PRIMARY KEY,
            booking_date DATE,
            amount DECIMAL(12,2),
            currency VARCHAR,
            counterpart VARCHAR,
            description VARCHAR,
            bank_name VARCHAR,
            synced_at TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS bitpanda_wallets (
            id VARCHAR PRIMARY KEY,
            wallet_name VARCHAR,
            asset_symbol VARCHAR,
            asset_type VARCHAR,
            balance DECIMAL(18,8),
            balance_eur DECIMAL(12,2),
            is_default BOOLEAN,
            synced_at TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS bitpanda_trades (
            id VARCHAR PRIMARY KEY,
            trade_date DATE,
            type VARCHAR,
            asset_symbol VARCHAR,
            asset_type VARCHAR,
            shares DECIMAL(18,8),
            price_eur DECIMAL(12,4),
            total_eur DECIMAL(12,2),
            fee_eur DECIMAL(12,4),
            synced_at TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            snapshot_date DATE,
            asset_symbol VARCHAR,
            asset_type VARCHAR,
            quantity DECIMAL(18,8),
            value_eur DECIMAL(12,2),
            PRIMARY KEY (snapshot_date, asset_symbol)
        )
    """)

    con.execute("""
        CREATE VIEW IF NOT EXISTS net_worth AS
        SELECT
            snapshot_date,
            SUM(value_eur) as total_value_eur
        FROM portfolio_snapshots
        GROUP BY snapshot_date
    """)

    con.close()
    print("Datenbank initialisiert")


if __name__ == "__main__":
    init_database()

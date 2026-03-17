# etl_pipeline.py
"""
Main ETL pipeline for syncing financial data to DuckDB warehouse.
Fetches data from all configured sources and stores in normalized format.
"""

import duckdb
from datetime import datetime
from bitpanda_connector import store_bitpanda_trades
from fints_connector import BankManager
from config import FINTS_BANKS


def store_bank_transactions():
    """
    Fetch transactions from all enabled FinTS banks and store in database.
    Automatically deduplicates based on transaction ID.
    """
    try:
        con = duckdb.connect("finance.duckdb")

        # Ensure table exists
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

        # Initialize bank manager with all enabled banks
        manager = BankManager(FINTS_BANKS)

        if not manager.banks:
            print("[WARN] No banks configured or enabled in config.py")
            return

        print(f"Connected to {len(manager.banks)} bank(s)")

        # Fetch transactions from all banks
        all_transactions = manager.fetch_all_transactions(days_back=90)

        # Store transactions (deduplicate)
        total_inserted = 0
        total_skipped = 0

        for txn in all_transactions:
            # Check if transaction already exists
            exists = con.execute(
                "SELECT COUNT(*) FROM bank_transactions WHERE id = ?",
                [txn['id']]
            ).fetchone()[0]

            if exists:
                total_skipped += 1
                continue

            # Insert new transaction
            con.execute("""
                INSERT INTO bank_transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                txn['id'],
                txn['booking_date'],
                txn['amount'],
                txn['currency'],
                txn['counterpart'],
                txn['description'],
                txn['bank_name'],
                datetime.now()
            ])
            total_inserted += 1

        print(f"[OK] Stored {total_inserted} new transactions (skipped {total_skipped} duplicates)")

        con.close()

    except Exception as e:
        print(f"[ERROR] Bank transactions error: {e}")
        import traceback
        traceback.print_exc()


def show_summary():
    """Display summary statistics after ETL run"""
    try:
        con = duckdb.connect("finance.duckdb")

        # Transaction counts by bank
        print("\n=== Summary ===")
        result = con.execute("""
            SELECT
                bank_name,
                COUNT(*) as transaction_count,
                MIN(booking_date) as earliest,
                MAX(booking_date) as latest,
                SUM(amount) as balance
            FROM bank_transactions
            GROUP BY bank_name
            ORDER BY bank_name
        """).fetchall()

        if result:
            print("\nBank Transactions:")
            for row in result:
                bank, count, earliest, latest, balance = row
                print(f"  {bank}: {count} transactions ({earliest} to {latest}), Balance: {balance:.2f} EUR")

        # Bitpanda summary
        wallet_count = con.execute("SELECT COUNT(*) FROM bitpanda_wallets").fetchone()[0]
        trade_count = con.execute("SELECT COUNT(*) FROM bitpanda_trades").fetchone()[0]

        if wallet_count or trade_count:
            print(f"\nBitpanda: {wallet_count} wallets, {trade_count} trades")

        con.close()

    except Exception as e:
        print(f"[ERROR] Summary error: {e}")


if __name__ == "__main__":
    print("=== ETL Pipeline Start ===\n")

    print("[1/2] Fetching Bitpanda data...")
    try:
        store_bitpanda_trades()
    except Exception as e:
        print(f"[ERROR] Bitpanda error: {e}")

    print("\n[2/2] Fetching bank transactions...")
    store_bank_transactions()

    # Show summary
    show_summary()

    print("\n=== ETL Pipeline Complete ===")

# etl_pipeline.py
"""
Main ETL pipeline for syncing financial data to DuckDB warehouse.
Supports multiple data sources: CSV, FinTS (optional), and Bitpanda.
Automatically detects available sources and fetches data.
"""

import duckdb
from datetime import datetime
import config


def store_bank_transactions():
    """
    Fetch transactions from all configured sources (CSV and optionally FinTS).
    Automatically deduplicates based on transaction ID.
    """
    all_transactions = []
    sources_used = []

    # 1. CSV Sources (Primary method)
    csv_sources = getattr(config, 'CSV_SOURCES', {})
    if csv_sources:
        try:
            from src.connectors.csv_connector import CSVBankManager
            print("Loading CSV sources...")
            csv_manager = CSVBankManager(csv_sources)

            if csv_manager.banks:
                csv_txns = csv_manager.fetch_all_transactions()
                all_transactions.extend(csv_txns)
                sources_used.append(f"CSV ({len(csv_manager.banks)} source(s))")
        except Exception as e:
            print(f"[ERROR] CSV loading failed: {e}")

    # 2. FinTS Sources (Optional)
    fints_enabled = getattr(config, 'FINTS_ENABLED', False)
    fints_banks = getattr(config, 'FINTS_BANKS', {})

    if fints_enabled and fints_banks:
        try:
            from src.connectors.optional.fints_connector import BankManager
            print("\nLoading FinTS sources...")
            fints_manager = BankManager(fints_banks)

            if fints_manager.banks:
                fints_txns = fints_manager.fetch_all_transactions(days_back=90)
                all_transactions.extend(fints_txns)
                sources_used.append(f"FinTS ({len(fints_manager.banks)} bank(s))")
        except ImportError:
            print("[INFO] FinTS not available (missing 'fints' library). Install with: pip install fints")
        except Exception as e:
            print(f"[ERROR] FinTS loading failed: {e}")

    # Check if any sources were loaded
    if not all_transactions:
        print("\n[WARN] No transactions loaded!")
        print("\nPlease configure at least one source in config.py:")
        print("  - CSV_SOURCES for CSV files (recommended)")
        print("  - FINTS_BANKS if you have FinTS access (optional)")
        return

    print(f"\n[OK] Loaded {len(all_transactions)} transactions from: {', '.join(sources_used)}")

    # Store in database
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
        print(f"[ERROR] Database error: {e}")
        import traceback
        traceback.print_exc()


def store_broker_orders():
    """
    Fetch orders from all configured broker sources.
    Automatically deduplicates based on order ID.
    """
    broker_sources = getattr(config, 'BROKER_SOURCES', {})
    if not broker_sources or not any(s.get('enabled') for s in broker_sources.values()):
        return

    try:
        from src.connectors.broker_connector import BrokerManager
        print("Loading broker sources...")
        broker_manager = BrokerManager(broker_sources)

        if not broker_manager.brokers:
            return

        all_orders = broker_manager.fetch_all_orders()

        if not all_orders:
            print("[INFO] No orders loaded from brokers.")
            return

        print(f"\n[OK] Loaded {len(all_orders)} orders")

        # Store in database
        con = duckdb.connect("finance.duckdb")

        # Ensure table exists
        con.execute("""
            CREATE TABLE IF NOT EXISTS securities_orders (
                id VARCHAR PRIMARY KEY,
                broker_name VARCHAR,
                security_name VARCHAR,
                isin VARCHAR,
                wkn VARCHAR,
                direction VARCHAR,
                quantity DECIMAL(18,8),
                quantity_executed DECIMAL(18,8),
                order_type VARCHAR,
                status VARCHAR,
                value DECIMAL(12,2),
                execution_price DECIMAL(12,4),
                execution_date DATE,
                created_date DATE,
                currency VARCHAR,
                synced_at TIMESTAMP
            )
        """)

        # Store orders (deduplicate)
        total_inserted = 0
        total_skipped = 0

        for order in all_orders:
            exists = con.execute(
                "SELECT COUNT(*) FROM securities_orders WHERE id = ?",
                [order['id']]
            ).fetchone()[0]

            if exists:
                total_skipped += 1
                continue

            con.execute("""
                INSERT INTO securities_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                order['id'],
                order['broker_name'],
                order['security_name'],
                order['isin'],
                order['wkn'],
                order['direction'],
                order['quantity'],
                order['quantity_executed'],
                order['order_type'],
                order['status'],
                order['value'],
                order['execution_price'],
                order['execution_date'],
                order['created_date'],
                order['currency'],
                datetime.now()
            ])
            total_inserted += 1

        print(f"[OK] Stored {total_inserted} new orders (skipped {total_skipped} duplicates)")
        con.close()

    except Exception as e:
        print(f"[ERROR] Broker orders error: {e}")
        import traceback
        traceback.print_exc()


def show_summary():
    """Display summary statistics after ETL run"""
    try:
        con = duckdb.connect("finance.duckdb")

        print("\n=== Summary ===")

        # Bank transactions summary
        try:
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
            else:
                print("\n[INFO] No bank transactions in database yet.")
        except Exception as e:
            print("\n[INFO] No bank transactions in database yet.")

        # Securities orders summary
        try:
            order_result = con.execute("""
                SELECT
                    broker_name,
                    COUNT(*) as order_count,
                    MIN(execution_date) as earliest,
                    MAX(execution_date) as latest
                FROM securities_orders
                WHERE execution_date IS NOT NULL
                GROUP BY broker_name
                ORDER BY broker_name
            """).fetchall()

            if order_result:
                print("\nSecurities Orders:")
                for row in order_result:
                    broker, count, earliest, latest = row
                    print(f"  {broker}: {count} orders ({earliest} to {latest})")
        except Exception as e:
            pass  # Table might not exist yet

        # Bitpanda summary (if enabled)
        try:
            wallet_count = con.execute("SELECT COUNT(*) FROM bitpanda_wallets").fetchone()[0]
            trade_count = con.execute("SELECT COUNT(*) FROM bitpanda_trades").fetchone()[0]

            if wallet_count or trade_count:
                print(f"\nBitpanda: {wallet_count} wallets, {trade_count} trades")
        except Exception as e:
            pass  # Tables might not exist yet

        con.close()

    except Exception as e:
        print(f"[ERROR] Summary error: {e}")


if __name__ == "__main__":
    try:
        print("=== ETL Pipeline Start ===\n")

        # Step 1: Bitpanda (if enabled)
        bitpanda_enabled = getattr(config, 'BITPANDA_ENABLED', False)
        if bitpanda_enabled:
            print("[1/3] Fetching Bitpanda data...")
            try:
                from src.connectors.bitpanda_connector import store_bitpanda_trades
                store_bitpanda_trades()
            except Exception as e:
                print(f"[ERROR] Bitpanda error: {e}")
        else:
            print("[1/3] Bitpanda disabled (set BITPANDA_ENABLED=True in config.py)")

        # Step 2: Bank transactions (CSV and/or FinTS)
        print("\n[2/3] Fetching bank transactions...")
        store_bank_transactions()

        # Step 3: Broker orders (securities)
        print("\n[3/3] Fetching broker orders...")
        store_broker_orders()

        # Show summary
        show_summary()

        print("\n=== ETL Pipeline Complete ===")

    except KeyboardInterrupt:
        print("\n\n[WARN] Pipeline interrupted by user (Ctrl+C)")
        print("=== ETL Pipeline Stopped ===")

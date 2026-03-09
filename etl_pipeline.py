from bitpanda_connector import store_bitpanda_trades
from gocardless_connector import fetch_transactions
from config import REVOLUT_REQUISITION_ID, C24_REQUISITION_ID
import duckdb
from datetime import datetime


def store_bank_transactions():
    try:
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

        for req_id, bank_name in [(REVOLUT_REQUISITION_ID, "Revolut"),
                                   (C24_REQUISITION_ID, "C24")]:
            if not req_id:
                print(f"⊘ {bank_name}: Keine Requisition ID konfiguriert")
                continue

            try:
                txns = fetch_transactions(req_id)
                inserted = 0

                for txn in txns:
                    txn_id = txn.get("transactionId") or txn.get("internalTransactionId")

                    exists = con.execute(
                        "SELECT COUNT(*) FROM bank_transactions WHERE id = ?",
                        [txn_id]
                    ).fetchone()[0]

                    if exists:
                        continue

                    con.execute("""
                        INSERT INTO bank_transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        txn_id,
                        txn.get("bookingDate"),
                        float(txn.get("transactionAmount", {}).get("amount", 0)),
                        txn.get("transactionAmount", {}).get("currency"),
                        txn.get("creditorName") or txn.get("debtorName"),
                        txn.get("remittanceInformationUnstructured", ""),
                        bank_name,
                        datetime.now()
                    ])
                    inserted += 1

                print(f"✓ {bank_name}: {inserted} neue Transaktionen")

            except Exception as e:
                print(f"✗ {bank_name} Fehler: {e}")

        con.close()

    except Exception as e:
        print(f"✗ Bank-Transaktionen Fehler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=== ETL Pipeline Start ===\n")

    print("[1/2] Lade Bitpanda Trades...")
    store_bitpanda_trades()

    print("\n[2/2] Lade Bank-Transaktionen...")
    store_bank_transactions()

    print("\n=== ETL Pipeline Complete ===")

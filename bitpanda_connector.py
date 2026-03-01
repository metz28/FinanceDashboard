# bitpanda_connector.py
import duckdb
import requests
from datetime import datetime

BITPANDA_API_KEY = "455e05d26d0fdf983fb4eae2a85ff851e3a27fe41f4251bc562802079c9e10f396b23aa38fe449b423c9a5e65189f9f988a7251ad98bd44baf300560366f4e52"
BASE_URL = "https://api.bitpanda.com/v1"
HEADERS = {"X-API-KEY": BITPANDA_API_KEY}


def fetch_trades(cursor=None):
    params = {"page_size": 100}
    if cursor:
        params["cursor"] = cursor
    r = requests.get(f"{BASE_URL}/trades", headers=HEADERS, params=params)
    data = r.json()
    
    # DEBUG - zeigt was die API wirklich zurückgibt
    print("API Response:", data)
    
    return data["data"], data.get("meta", {}).get("next_cursor")


def fetch_all_trades():
    all_trades, cursor = [], None
    while True:
        trades, cursor = fetch_trades(cursor)
        all_trades.extend(trades)
        if not cursor:
            break
    return all_trades


def store_bitpanda_trades():
    con = duckdb.connect("finance.duckdb")
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

    trades = fetch_all_trades()
    inserted = 0
    skipped = 0

    for trade in trades:
        attr = trade.get("attributes", {})
        trade_id = trade.get("id")

        exists = con.execute(
            "SELECT COUNT(*) FROM bitpanda_trades WHERE id = ?",
            [trade_id]
        ).fetchone()[0]

        if exists:
            skipped += 1
            continue

        con.execute("""
            INSERT INTO bitpanda_trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            trade_id,
            attr.get("time", {}).get("date_iso8601", "")[:10],
            attr.get("type"),
            attr.get("cryptocoin_symbol") or attr.get("asset_symbol"),
            attr.get("type_string"),
            float(attr.get("amount_cryptocoin", 0)),
            float(attr.get("price", 0)),
            float(attr.get("amount_fiat", 0)),
            float(attr.get("fee", {}).get("amount", 0)),
            datetime.now()
        ])
        inserted += 1

    con.close()
    print(f"✓ {inserted} neue Trades gespeichert, {skipped} bereits vorhanden")
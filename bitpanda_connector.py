# bitpanda_connector.py
import duckdb
import requests
from datetime import datetime
from config import BITPANDA_API_KEY
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://api.bitpanda.com/v1"
HEADERS = {"X-API-KEY": BITPANDA_API_KEY}

#TODO add fetch_wallet

def fetch_wallets(cursor=None):
    params = {"page_size": 100}
    if cursor:
        params["cursor"] = cursor

    try:
        r = requests.get(
            f"{BASE_URL}/wallets",
            params=params,
            headers=HEADERS,
            verify=True,
            timeout=30
        )
        r.raise_for_status()
        return r.json()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("✗ Unauthorized: API Key ist ungültig")
        else:
            print(f"✗ HTTP-Fehler {e.response.status_code}: {e}")
        return {"data": []}
    except requests.exceptions.RequestException as e:
        print(f"✗ Netzwerk-Fehler: {e}")
        return {"data": []}


def fetch_trades(cursor=None):
    params = {"page_size": 100}
    if cursor:
        params["cursor"] = cursor

    try:
        r = requests.get(
            f"{BASE_URL}/trades",
            headers=HEADERS,
            params=params,
            verify=True,
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
        return data["data"], data.get("meta", {}).get("next_cursor")
    except requests.exceptions.SSLError:
        print("⚠ SSL-Fehler - versuche ohne Zertifikatsprüfung...")
        try:
            r = requests.get(
                f"{BASE_URL}/trades",
                headers=HEADERS,
                params=params,
                verify=False,
                timeout=30
            )
            r.raise_for_status()
            data = r.json()
            return data["data"], data.get("meta", {}).get("next_cursor")
        except requests.exceptions.HTTPError as e:
            if r.status_code == 401:
                print(f"✗ Authentifizierungs-Fehler: API Key ist falsch oder ungültig")
                print(f"  Aktueller Key: {BITPANDA_API_KEY[:10]}...")
                print(f"  Bitte korrekten API Key in config.py eintragen!")
            elif r.status_code == 403:
                print(f"✗ Zugriff verweigert: API Key hat keine Berechtigung für Trades")
            else:
                print(f"✗ HTTP-Fehler {r.status_code}: {e}")
            return [], None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"✗ Authentifizierungs-Fehler: API Key ist falsch oder ungültig")
            print(f"  Aktueller Key: {BITPANDA_API_KEY[:10]}...")
            print(f"  Bitte korrekten API Key in config.py eintragen!")
        elif e.response.status_code == 403:
            print(f"✗ Zugriff verweigert: API Key hat keine Berechtigung für Trades")
        else:
            print(f"✗ HTTP-Fehler {e.response.status_code}: {e}")
        return [], None
    except requests.exceptions.Timeout:
        print(f"✗ Timeout: Bitpanda API antwortet nicht")
        return [], None
    except requests.exceptions.RequestException as e:
        print(f"✗ Netzwerk-Fehler: {e}")
        return [], None


def fetch_all_trades():
    all_trades, cursor = [], None
    while True:
        trades, cursor = fetch_trades(cursor)
        all_trades.extend(trades)
        if not cursor:
            break
    return all_trades


def table_exists(con, table_name):
    result = con.execute(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = ?)",
        [table_name]
    ).fetchone()[0]
    return result

def store_bitpanda_wallets():

    try:
        con = duckdb.connect("finance.duckdb")

        if not table_exists(con, "bitpanda_wallets"):
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

        wallets_data = fetch_wallets()

        if not wallets_data or not wallets_data.get("data"):
            print("⚠ Keine Bitpanda Wallets gefunden oder API-Fehler")
            con.close()
            return

        wallets = wallets_data.get("data", [])
        inserted = 0
        updated = 0

        for wallet in wallets:
            attr = wallet.get("attributes", {})
            wallet_id = wallet.get("id")

            exists = con.execute(
                "SELECT COUNT(*) FROM bitpanda_wallets WHERE id = ?",
                [wallet_id]
            ).fetchone()[0]

            if exists:
                con.execute("""
                    UPDATE bitpanda_wallets
                    SET balance = ?, balance_eur = ?, synced_at = ?
                    WHERE id = ?
                """, [
                    float(attr.get("balance", 0)),
                    float(attr.get("balance_eur", 0)),
                    datetime.now(),
                    wallet_id
                ])
                updated += 1
            else:
                con.execute("""
                    INSERT INTO bitpanda_wallets VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    wallet_id,
                    attr.get("name"),
                    attr.get("cryptocoin_symbol") or attr.get("fiat_symbol"),
                    attr.get("type"),
                    float(attr.get("balance", 0)),
                    float(attr.get("balance_eur", 0)),
                    attr.get("is_default", False),
                    datetime.now()
                ])
                inserted += 1

        con.close()
        print(f"✓ Bitpanda Wallets: {inserted} neu, {updated} aktualisiert")

    except Exception as e:
        print(f"✗ Bitpanda Wallets Fehler: {e}")
        import traceback
        traceback.print_exc()


def store_bitpanda_trades():

    try:
        con = duckdb.connect("finance.duckdb")

        if not table_exists(con, "bitpanda_trades"):
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

        if not trades:
            print("⚠ Keine Bitpanda Trades gefunden oder API-Fehler")
            con.close()
            return

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
        print(f"✓ Bitpanda: {inserted} neue Trades gespeichert, {skipped} bereits vorhanden")

    except Exception as e:
        print(f"✗ Bitpanda Fehler: {e}")
        import traceback
        traceback.print_exc()

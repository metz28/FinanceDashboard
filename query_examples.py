#!/usr/bin/env python3
"""
Beispiel-Queries für FinanceDashboard
Zeigt verschiedene Möglichkeiten Daten aus der Datenbank abzufragen.
"""

import duckdb
import pandas as pd

# Verbindung zur Datenbank
con = duckdb.connect("finance.duckdb")

print("=" * 60)
print("FinanceDashboard - Beispiel Queries")
print("=" * 60)

# =============================================================================
# 1. Alle verfügbaren Tabellen anzeigen
# =============================================================================
print("\n1. Verfügbare Tabellen:")
print("-" * 60)
tables = con.execute("SHOW TABLES").df()
print(tables)

# =============================================================================
# 2. Bank-Transaktionen
# =============================================================================
print("\n2. Letzte 10 Bank-Transaktionen:")
print("-" * 60)
try:
    recent_txns = con.execute("""
        SELECT
            booking_date,
            bank_name,
            amount,
            counterpart,
            description
        FROM bank_transactions
        ORDER BY booking_date DESC
        LIMIT 10
    """).df()
    print(recent_txns)
except Exception as e:
    print(f"Keine Daten: {e}")

# =============================================================================
# 3. Kontostand pro Bank
# =============================================================================
print("\n3. Kontostand pro Bank:")
print("-" * 60)
try:
    balance = con.execute("""
        SELECT
            bank_name,
            COUNT(*) as anzahl_transaktionen,
            SUM(amount) as kontostand,
            MIN(booking_date) as erste_transaktion,
            MAX(booking_date) as letzte_transaktion
        FROM bank_transactions
        GROUP BY bank_name
    """).df()
    print(balance)
except Exception as e:
    print(f"Keine Daten: {e}")

# =============================================================================
# 4. Monatliche Ausgaben/Einnahmen
# =============================================================================
print("\n4. Monatliche Ausgaben und Einnahmen:")
print("-" * 60)
try:
    monthly = con.execute("""
        SELECT
            DATE_TRUNC('month', booking_date) as monat,
            SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as ausgaben,
            SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as einnahmen,
            SUM(amount) as saldo
        FROM bank_transactions
        GROUP BY monat
        ORDER BY monat DESC
        LIMIT 12
    """).df()
    print(monthly)
except Exception as e:
    print(f"Keine Daten: {e}")

# =============================================================================
# 5. Top 10 Ausgaben
# =============================================================================
print("\n5. Top 10 Ausgaben:")
print("-" * 60)
try:
    top_expenses = con.execute("""
        SELECT
            booking_date,
            counterpart,
            amount,
            description
        FROM bank_transactions
        WHERE amount < 0
        ORDER BY amount ASC
        LIMIT 10
    """).df()
    print(top_expenses)
except Exception as e:
    print(f"Keine Daten: {e}")

# =============================================================================
# 6. Wertpapier-Orders (falls vorhanden)
# =============================================================================
print("\n6. Wertpapier-Orders:")
print("-" * 60)
try:
    orders = con.execute("""
        SELECT
            execution_date,
            direction,
            security_name,
            quantity_executed,
            execution_price,
            value
        FROM securities_orders
        WHERE status = 'Ausgeführt'
        ORDER BY execution_date DESC
        LIMIT 10
    """).df()
    print(orders)
except Exception as e:
    print(f"Keine Orders: {e}")

# =============================================================================
# 7. Aktuelles Wertpapier-Portfolio
# =============================================================================
print("\n7. Aktuelles Portfolio (View):")
print("-" * 60)
try:
    portfolio = con.execute("""
        SELECT
            security_name,
            isin,
            total_quantity,
            avg_price,
            total_quantity * avg_price as portfolio_wert
        FROM securities_portfolio
        ORDER BY portfolio_wert DESC
    """).df()
    print(portfolio)
except Exception as e:
    print(f"Kein Portfolio: {e}")

# =============================================================================
# 8. Bitpanda Crypto (falls aktiviert)
# =============================================================================
print("\n8. Bitpanda Wallets:")
print("-" * 60)
try:
    crypto = con.execute("""
        SELECT
            asset_symbol,
            balance,
            balance_eur
        FROM bitpanda_wallets
        WHERE balance > 0
        ORDER BY balance_eur DESC
    """).df()
    print(crypto)
except Exception as e:
    print(f"Kein Crypto: {e}")

# =============================================================================
# 9. Gesamt-Übersicht
# =============================================================================
print("\n9. Gesamt-Übersicht:")
print("-" * 60)

try:
    # Bank-Guthaben
    bank_total = con.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM bank_transactions
    """).fetchone()[0]
    print(f"Bank-Konten gesamt: {bank_total:.2f} EUR")
except:
    bank_total = 0
    print("Bank-Konten gesamt: 0.00 EUR")

try:
    # Depot-Wert (vereinfacht)
    depot_total = con.execute("""
        SELECT COALESCE(SUM(total_quantity * avg_price), 0) as total
        FROM securities_portfolio
    """).fetchone()[0]
    print(f"Depot-Wert: {depot_total:.2f} EUR")
except:
    depot_total = 0
    print("Depot-Wert: 0.00 EUR")

try:
    # Crypto-Wert
    crypto_total = con.execute("""
        SELECT COALESCE(SUM(balance_eur), 0) as total
        FROM bitpanda_wallets
    """).fetchone()[0]
    print(f"Crypto-Wert: {crypto_total:.2f} EUR")
except:
    crypto_total = 0
    print("Crypto-Wert: 0.00 EUR")

print(f"\nGesamtvermögen: {bank_total + depot_total + crypto_total:.2f} EUR")

# =============================================================================
# 10. Eigene Query ausführen
# =============================================================================
print("\n" + "=" * 60)
print("Eigene Query ausführen:")
print("-" * 60)

# Beispiel für eigene Query
custom_query = """
    SELECT
        booking_date,
        counterpart,
        amount
    FROM bank_transactions
    WHERE amount > 100
    ORDER BY amount DESC
    LIMIT 5
"""

print(f"Query:\n{custom_query}")
print("\nErgebnis:")
try:
    result = con.execute(custom_query).df()
    print(result)
except Exception as e:
    print(f"Fehler: {e}")

# Verbindung schließen
con.close()

print("\n" + "=" * 60)
print("Fertig!")
print("=" * 60)

# Quick Start mit Broker-Orders (Finanzen Zero)

Import von Wertpapier-Orders aus Finanzen Zero oder anderen Brokern.

## Was wird importiert?

- Kauf- und Verkaufs-Orders
- ISIN, WKN, Wertpapier-Name
- Anzahl, Ausführungskurs, Gesamt-Wert
- Order-Status, Order-Typ (Market, Limit, etc.)
- Ausführungs- und Erstellungsdatum

## 1. CSV aus Finanzen Zero exportieren

1. Logge dich in dein Finanzen Zero Konto ein
2. Gehe zu "Orders" oder "Order-Historie"
3. Exportiere als CSV
4. Speichere als `data/finanzen_zero_orders.csv`

## 2. Config anpassen

Öffne `config.py` und aktiviere Broker-Import:

```python
BROKER_SOURCES = {
    'finanzen_zero': {
        'name': 'Finanzen Zero',
        'csv_path': 'data/finanzen_zero_orders.csv',
        'format': 'finanzen_zero',
        'enabled': True  # Wichtig: auf True setzen!
    }
}
```

## 3. Datenbank initialisieren (falls noch nicht geschehen)

```bash
python src/database/warehouse.py
```

Dies erstellt die Tabelle `securities_orders`.

## 4. Pipeline ausführen

```bash
python etl_pipeline.py
```

**Erwartete Ausgabe:**
```
=== ETL Pipeline Start ===

[1/3] Bitpanda disabled (set BITPANDA_ENABLED=True in config.py)

[2/3] Fetching bank transactions...
Loading CSV sources...
...

[3/3] Fetching broker orders...
Loading broker sources...
[BROKER] Loaded: Finanzen Zero
Lese Orders von Finanzen Zero...
  [OK] 45 Orders aus finanzen_zero_orders.csv

[OK] Loaded 45 orders
[OK] Stored 45 new orders (skipped 0 duplicates)

=== Summary ===
...
Securities Orders:
  Finanzen Zero: 45 orders (2024-01-01 to 2024-03-29)

=== ETL Pipeline Complete ===
```

## 5. Daten abfragen

### Python

```python
import duckdb
con = duckdb.connect("finance.duckdb")

# Alle ausgeführten Orders
df = con.execute("""
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

print(df)
```

### Aktuelles Portfolio (View)

```python
# Zeigt dein aktuelles Depot basierend auf Käufen/Verkäufen
portfolio = con.execute("""
    SELECT * FROM securities_portfolio
    ORDER BY total_quantity * avg_price DESC
""").df()

print(portfolio)
```

Das `securities_portfolio` View berechnet automatisch:
- Aktuelle Anzahl pro Wertpapier (Käufe - Verkäufe)
- Durchschnittlicher Einkaufspreis
- Filtert automatisch verkaufte Positionen raus

### Weitere nützliche Queries

**Käufe vs. Verkäufe:**
```sql
SELECT
    direction,
    COUNT(*) as anzahl_orders,
    SUM(value) as gesamt_wert
FROM securities_orders
WHERE status = 'Ausgeführt'
GROUP BY direction;
```

**Top 5 Positionen nach Wert:**
```sql
SELECT
    security_name,
    isin,
    SUM(quantity_executed) as gesamt_anzahl,
    AVG(execution_price) as avg_preis,
    SUM(value) as gesamt_investiert
FROM securities_orders
WHERE status = 'Ausgeführt' AND direction = 'Kauf'
GROUP BY security_name, isin
ORDER BY gesamt_investiert DESC
LIMIT 5;
```

**Orders nach Monat:**
```sql
SELECT
    DATE_TRUNC('month', execution_date) as monat,
    COUNT(*) as anzahl_orders,
    SUM(value) as gesamt_wert
FROM securities_orders
WHERE status = 'Ausgeführt'
GROUP BY monat
ORDER BY monat DESC;
```

## CSV-Format Details

### Finanzen Zero Format

Das CSV verwendet Semikolon (`;`) als Delimiter:

```
Name;ISIN;WKN;Anzahl;Anzahl storniert;Status;Orderart;Limit;Stop;Erstellt Datum;Erstellt Zeit;Gültig bis;Richtung;Wert;Wert storniert;Mindermengenzuschlag;Ausführung Datum;Ausführung Zeit;Ausführung Kurs;Anzahl ausgeführt;Anzahl offen;Gestrichen Datum;Gestrichen Zeit
```

Beispiel:
```csv
Apple Inc.;US0378331005;865985;10;0;Ausgeführt;Market;;;01.01.2024;10:30:00;31.12.2024;Kauf;1850,00;0,00;0,00;01.01.2024;10:31:05;185,00;10;0;;
```

### Trade Republic / Andere Broker

Für andere Broker kannst du ein generic Format definieren:

```python
BROKER_SOURCES = {
    'trade_republic': {
        'name': 'Trade Republic',
        'csv_path': 'data/trade_republic_orders.csv',
        'format': 'generic',  # Verwendet minimales Feld-Mapping
        'enabled': True
    }
}
```

## Mehrere Broker gleichzeitig

```python
BROKER_SOURCES = {
    'finanzen_zero': {
        'name': 'Finanzen Zero',
        'csv_path': 'data/finanzen_zero_orders.csv',
        'format': 'finanzen_zero',
        'enabled': True
    },
    'trade_republic': {
        'name': 'Trade Republic',
        'csv_path': 'data/trade_republic_orders.csv',
        'format': 'generic',
        'enabled': True
    }
}
```

Alle Orders werden in einer Tabelle zusammengeführt!

## Kombiniert mit Bank-Transaktionen

Du kannst gleichzeitig Bank-Transaktionen UND Broker-Orders importieren:

```python
# Bank-Transaktionen (Girokonto, etc.)
CSV_SOURCES = {
    'c24': {
        'name': 'C24 Bank',
        'csv_path': 'data/c24_transactions.csv',
        'format': 'c24',
        'enabled': True
    }
}

# Wertpapier-Orders (Depot)
BROKER_SOURCES = {
    'finanzen_zero': {
        'name': 'Finanzen Zero',
        'csv_path': 'data/finanzen_zero_orders.csv',
        'format': 'finanzen_zero',
        'enabled': True
    }
}
```

Die Pipeline lädt beides automatisch!

## Beispiel-Datei

Siehe `data/example_finanzen_zero.csv` für ein Beispiel-CSV mit Test-Daten.

## Vorteile

- ✅ Komplette Order-Historie an einem Ort
- ✅ Portfolio-Tracking über alle Broker hinweg
- ✅ Automatische Berechnung von Kauf/Verkauf-Bilanz
- ✅ SQL-Queries für detaillierte Analysen
- ✅ Kombinierbar mit Bank-Transaktionen und Krypto

# FinanceDashboard

Automatisiere das Sammeln deiner Finanzdaten von verschiedenen Quellen (Banken, Krypto) in einer zentralen DuckDB Datenbank.

## Features

- **Direkte Bankverbindung via FinTS** - Keine Drittanbieter-API nötig
- **Unterstützt alle großen deutschen Banken** - Sparkasse, DKB, ING, C24, etc.
- **Bitpanda Integration** - Automatischer Import von Krypto-Trades und Wallets
- **Lokales Data Warehouse** - Alle Daten in einer DuckDB Datenbank
- **Automatische Deduplizierung** - Keine doppelten Transaktionen
- **ETL Pipeline** - Einfaches Sync mit einem Befehl

## Projektstruktur

```
FinanceDashboard/
├── src/
│   ├── connectors/          # Bank- und API-Verbindungen
│   │   ├── fints_connector.py
│   │   └── bitpanda_connector.py
│   ├── database/            # Datenbank-Schema
│   │   └── warehouse.py
│   └── zero_pdf_parser.py
├── tests/
│   └── test_credentials.py
├── docs/
│   └── SETUP.md            # Detaillierte Einrichtungsanleitung
├── config.example.py        # Template für Konfiguration
├── config.py               # Deine Zugangsdaten (nicht in Git!)
├── etl_pipeline.py         # Haupt-ETL Script
├── requirements.txt
└── finance.duckdb          # Deine Datenbank
```

## Quick Start (CSV - Empfohlen)

Der einfachste Weg zu starten - ohne FinTS oder API Keys.

### 1. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 2. CSV aus deinem Online-Banking exportieren

1. Logge dich in dein Online-Banking ein
2. Exportiere Transaktionen als CSV
3. Speichere die Datei in `data/c24_transactions.csv`

### 3. Konfiguration erstellen

```bash
cp config.example.py config.py
```

Bearbeite `config.py` und konfiguriere CSV-Quellen:

```python
CSV_SOURCES = {
    'c24': {
        'name': 'C24 Bank',
        'csv_path': 'data/c24_transactions.csv',
        'format': 'c24',
        'enabled': True  # Aktivieren
    }
}
```

### 4. Datenbank initialisieren

```bash
python src/database/warehouse.py
```

### 5. ETL Pipeline ausführen

```bash
python etl_pipeline.py
```

Das war's! Deine Transaktionen sind jetzt in `finance.duckdb`.

**Detaillierte CSV-Anleitung:** Siehe [QUICKSTART_CSV.md](QUICKSTART_CSV.md)

---

## Alternative: FinTS (Optional)

Für direkte Bankverbindung siehe [docs/SETUP.md](docs/SETUP.md) - erfordert FinTS-Zugang.

```python
FINTS_ENABLED = True
FINTS_BANKS = {
    'c24': {
        'name': 'C24 Bank',
        'blz': '12030000',
        'username': 'dein_username',
        'pin': 'dein_pin',
        'enabled': True
    }
}
```

**BLZ Codes:**
- C24/DKB: `12030000`
- ING: `50010517`
- Commerzbank: `50040000`

Weitere: https://www.sparkasse.de/service/bankleitzahlen.html

## Bitpanda (Optional)

Für Krypto-Integration:

1. API Key holen: https://www.bitpanda.com/ → Account → API
2. In `config.py` eintragen:

```python
BITPANDA_API_KEY = "dein_api_key"
BITPANDA_ENABLED = True
```

3. Pipeline erneut ausführen: `python etl_pipeline.py`

## Daten abfragen

### Python

```python
import duckdb
con = duckdb.connect("finance.duckdb")

# Letzte 10 Transaktionen
con.execute("""
    SELECT booking_date, bank_name, amount, counterpart
    FROM bank_transactions
    ORDER BY booking_date DESC
    LIMIT 10
""").df()

# Monatliche Ausgaben
con.execute("""
    SELECT
        DATE_TRUNC('month', booking_date) as monat,
        SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as ausgaben,
        SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as einnahmen
    FROM bank_transactions
    GROUP BY monat
    ORDER BY monat DESC
""").df()
```

### DuckDB CLI

```bash
duckdb finance.duckdb

SELECT * FROM bank_transactions ORDER BY booking_date DESC LIMIT 10;
```

## Automatisierung

### Windows (Task Scheduler)

Täglich um 8:00 Uhr ausführen:

```powershell
schtasks /create /tn "FinanceETL" /tr "python C:\Users\maxis\Desktop\FinanceDashboard\etl_pipeline.py" /sc daily /st 08:00
```

### Linux/Mac (Cron)

```bash
crontab -e
```

Zeile hinzufügen:

```
0 8 * * * cd /path/to/FinanceDashboard && python etl_pipeline.py
```

## Sicherheit

- `config.py` ist bereits in `.gitignore` und wird nicht committed
- Nutze für zusätzliche Sicherheit Umgebungsvariablen (siehe `config.example.py`)
- Die Datenbank liegt lokal - keine Cloud-Synchronisation
- FinTS ist ein direktes, sicheres Protokoll zu deiner Bank

## Troubleshooting

**"Invalid credentials"**
- Username und PIN prüfen
- Manche Banken verwenden separate FinTS-PINs

**"Bank not supported"**
- Nicht alle Banken unterstützen FinTS (z.B. N26, Revolut)
- In der Bank-Dokumentation nach "FinTS" oder "HBCI" suchen

**"Connection timeout"**
- Manche Banken limitieren FinTS-Verbindungen
- Ein paar Minuten warten und erneut versuchen

**"TAN required"**
- Beim ersten Setup kann eine TAN erforderlich sein
- Script ausführen und TAN-Aufforderung folgen

## Detaillierte Dokumentation

Siehe [docs/SETUP.md](docs/SETUP.md) für:
- Schritt-für-Schritt Einrichtung
- Erweiterte SQL-Queries
- Weitere Banken hinzufügen
- Datenbankschema-Details

## Roadmap

- [ ] Kategorisierung von Transaktionen (ML-basiert)
- [ ] Visualisierungs-Dashboard (Streamlit/Plotly)
- [ ] Budget-Tracking
- [ ] Export zu Portfolio-Trackern
- [ ] Mehr Krypto-Exchanges (Kraken, Coinbase)

## Lizenz

MIT License - Verwende es wie du möchtest!

## Support

Bei Problemen oder Fragen erstelle ein Issue oder siehe die [docs/SETUP.md](docs/SETUP.md) Dokumentation.

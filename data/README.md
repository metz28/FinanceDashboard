# Data Ordner

Lege hier deine CSV-Dateien mit Bank-Transaktionen ab.

## Nutzung

1. Exportiere Transaktionen aus deinem Online-Banking als CSV
2. Speichere die CSV-Datei hier (z.B. `c24_transactions.csv`)
3. Trage den Pfad in `config.py` ein:

```python
CSV_SOURCES = {
    'c24': {
        'name': 'C24 Bank',
        'csv_path': 'data/c24_transactions.csv',
        'format': 'c24',
        'enabled': True
    }
}
```

4. Führe die ETL-Pipeline aus: `python etl_pipeline.py`

## Unterstützte Formate

### C24 Format

Das C24 CSV-Format enthält folgende Spalten:
- Transaktionstyp
- Buchungsdatum
- Karteneinsatz
- Betrag
- Zahlungsempfänger
- IBAN
- BIC
- Verwendungszweck
- Beschreibung
- Kontonummer
- Kontoname
- Kategorie
- Unterkategorie
- Bargeldabhebung

### Generic Format

Für andere Banken wird ein generisches Format unterstützt mit Mindestfeldern:
- Datum
- Betrag
- Empfänger
- Verwendungszweck

## Beispiel-Dateistruktur

```
data/
├── c24_transactions.csv
├── dkb_transactions.csv
└── ing_transactions.csv
```

**Hinweis:** Dieser Ordner ist in `.gitignore` und deine CSV-Dateien werden nicht in Git committed.

# Quick Start mit CSV

Die einfachste Methode um zu starten - ohne FinTS Zugang oder API Keys.

## 1. CSV aus Online-Banking exportieren

### C24 Bank

1. Logge dich in dein C24 Online-Banking ein
2. Gehe zu deinen Transaktionen
3. Klicke auf "Exportieren" oder "CSV Download"
4. Speichere die Datei als `c24_transactions.csv`

### Andere Banken

Die meisten Banken bieten CSV-Export an:
- **DKB**: Online-Banking → Umsätze → CSV Export
- **ING**: Online-Banking → Konto → Umsätze exportieren
- **Sparkasse**: Online-Banking → Umsätze → Export
- **Commerzbank**: Online-Banking → Kontoübersicht → CSV Export

## 2. CSV-Datei ablegen

Erstelle den `data/` Ordner (falls noch nicht vorhanden) und lege deine CSV dort ab:

```
FinanceDashboard/
└── data/
    └── c24_transactions.csv
```

## 3. Config anpassen

Öffne `config.py` und stelle sicher, dass `CSV_SOURCES` konfiguriert ist:

```python
CSV_SOURCES = {
    'c24': {
        'name': 'C24 Bank',
        'csv_path': 'data/c24_transactions.csv',
        'format': 'c24',
        'enabled': True  # Wichtig: auf True setzen!
    }
}
```

**Mehrere Banken?** Füge einfach weitere Einträge hinzu:

```python
CSV_SOURCES = {
    'c24': {
        'name': 'C24 Bank',
        'csv_path': 'data/c24_transactions.csv',
        'format': 'c24',
        'enabled': True
    },
    'dkb': {
        'name': 'DKB',
        'csv_path': 'data/dkb_transactions.csv',
        'format': 'generic',
        'enabled': True
    }
}
```

## 4. Pipeline ausführen

```bash
python etl_pipeline.py
```

Das war's! Deine Transaktionen sind jetzt in `finance.duckdb`.

## 5. Daten anschauen

### Python

```python
import duckdb
con = duckdb.connect("finance.duckdb")

# Letzte 10 Transaktionen
df = con.execute("""
    SELECT booking_date, bank_name, amount, counterpart
    FROM bank_transactions
    ORDER BY booking_date DESC
    LIMIT 10
""").df()

print(df)
```

### DuckDB CLI

```bash
duckdb finance.duckdb

SELECT * FROM bank_transactions ORDER BY booking_date DESC LIMIT 10;
```

## CSV-Format Details

### C24 Format

Das C24 CSV enthält diese Spalten:
```
Transaktionstyp,Buchungsdatum,Karteneinsatz,Betrag,Zahlungsempfänger,IBAN,BIC,Verwendungszweck,Beschreibung,Kontonummer,Kontoname,Kategorie,Unterkategorie,Bargeldabhebung
```

Beispiel:
```csv
Ausgehende Überweisung,01.01.2024,,"-123,45",REWE,DE123456789,COBADEFF,Einkauf,,12345,Girokonto,Lebensmittel,Supermarkt,
```

### Generic Format

Für andere Banken wird ein minimales Format unterstützt:
```
Datum,Betrag,Empfänger,Verwendungszweck
01.01.2024,-123.45,REWE,Einkauf
```

## CSV regelmäßig aktualisieren

### Manuell

1. Exportiere neue Transaktionen aus Online-Banking
2. Ersetze die CSV-Datei im `data/` Ordner
3. Führe `python etl_pipeline.py` aus
4. Duplikate werden automatisch erkannt und übersprungen!

### Automatisch

Manche Banken bieten APIs oder E-Mail-Benachrichtigungen mit CSV-Anhang. Diese kannst du automatisiert ins `data/` Verzeichnis legen.

## Mehrere CSV-Dateien

Du kannst auch einen ganzen Ordner mit CSVs angeben:

```python
CSV_SOURCES = {
    'c24': {
        'name': 'C24 Bank',
        'csv_path': 'data/c24/',  # Ordner statt Datei
        'format': 'c24',
        'enabled': True
    }
}
```

Alle `.csv` Dateien im Ordner werden automatisch geladen.

## Vorteile von CSV

- ✅ Sofort startbereit
- ✅ Keine API Keys nötig
- ✅ Keine FinTS Freischaltung erforderlich
- ✅ Funktioniert mit jeder Bank
- ✅ Volle Kontrolle über deine Daten

## Nachteile von CSV

- ❌ Manueller Export notwendig
- ❌ Keine Echtzeit-Daten
- ❌ Kontostand muss manuell berechnet werden

## Später zu FinTS wechseln?

Kein Problem! Beide Methoden funktionieren parallel:

```python
# Beides gleichzeitig möglich
CSV_SOURCES = {
    'c24': {
        'name': 'C24 Bank',
        'csv_path': 'data/c24_transactions.csv',
        'format': 'c24',
        'enabled': True
    }
}

FINTS_ENABLED = True
FINTS_BANKS = {
    'dkb': {
        'name': 'DKB',
        'blz': '12030000',
        'username': 'your_username',
        'pin': 'your_pin',
        'enabled': True
    }
}
```

Die Pipeline lädt automatisch aus beiden Quellen!

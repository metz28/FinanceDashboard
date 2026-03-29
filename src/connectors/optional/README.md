# Optional Connectors

Dieser Ordner enthält optionale Bank-Connectoren die zusätzliche Dependencies oder kostenpflichtige Zugänge erfordern.

## FinTS Connector

**Status:** Optional / Erfordert FinTS-Zugang

Der FinTS-Connector ermöglicht direkten Zugriff auf deutsche Banken über das FinTS/HBCI-Protokoll.

### Voraussetzungen

1. **FinTS-Unterstützung der Bank**: Nicht alle Banken unterstützen FinTS (z.B. N26, Revolut nicht verfügbar)
2. **FinTS-Freischaltung**: Manche Banken erfordern separate Freischaltung im Online-Banking
3. **Python-Library**: `pip install fints`

### Verwendung

Wenn du FinTS nutzen möchtest:

1. Installiere Dependencies:
   ```bash
   pip install fints
   ```

2. Aktiviere in `config.py`:
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

3. Die ETL-Pipeline erkennt automatisch ob FinTS verfügbar ist

### Alternative: CSV-Import

Für den Anfang oder wenn FinTS nicht verfügbar ist, nutze den **CSV-Connector**:

```python
CSV_SOURCES = {
    'c24': {
        'name': 'C24 Bank',
        'csv_path': 'pfad/zu/c24_transaktionen.csv',
        'format': 'c24',
        'enabled': True
    }
}
```

Der CSV-Connector ist immer verfügbar und erfordert keine zusätzlichen Freischaltungen.

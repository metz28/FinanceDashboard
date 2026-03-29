# config.example.py
# Template für Konfigurationsdatei - kopiere diese Datei zu config.py und trage deine Daten ein

# ============================================================================
# CSV SOURCES (Empfohlen für den Start)
# ============================================================================
# Lade Bank-Transaktionen aus CSV-Dateien.
# Exportiere die CSV aus deinem Online-Banking und gib hier den Pfad an.

CSV_SOURCES = {
    'c24': {
        'name': 'C24 Bank',
        'csv_path': 'data/c24_transactions.csv',  # Pfad zur CSV-Datei oder Ordner mit CSVs
        'format': 'c24',  # Format: 'c24', 'generic'
        'enabled': True   # Auf True setzen um zu aktivieren
    },
    # Weitere Banken hinzufügen:
    # 'dkb': {
    #     'name': 'DKB',
    #     'csv_path': 'data/dkb_transactions.csv',
    #     'format': 'generic',
    #     'enabled': True
    # }
}

# ============================================================================
# FinTS Banks (OPTIONAL - Erfordert FinTS-Zugang)
# ============================================================================
# FinTS ermöglicht direkte Verbindung zu deutschen Banken.
# Achtung: Nicht alle Banken unterstützen FinTS, manche erfordern Freischaltung.
# Alternative: Nutze CSV_SOURCES (siehe oben) für einfachen CSV-Import.

FINTS_ENABLED = False  # Setze auf True wenn du FinTS nutzen möchtest

FINTS_BANKS = {
    'c24': {
        'name': 'C24 Bank',
        'blz': '12030000',              # Bankleitzahl
        'username': 'your_username',    # Online-Banking Benutzername
        'pin': 'your_pin',              # Online-Banking PIN
        'enabled': False,               # Auf True setzen wenn FinTS verfügbar
        'product_id': 'FinanceDashboard'
    },
    # Weitere Banken:
    # 'dkb': {
    #     'name': 'DKB',
    #     'blz': '12030000',
    #     'username': 'dkb_username',
    #     'pin': 'dkb_pin',
    #     'enabled': True
    # }
}

# ============================================================================
# BROKER SOURCES (Wertpapier-Orders)
# ============================================================================
# Lade Wertpapier-Orders aus CSV-Dateien (Finanzen Zero, Trade Republic, etc.).

BROKER_SOURCES = {
    'finanzen_zero': {
        'name': 'Finanzen Zero',
        'csv_path': 'data/finanzen_zero_orders.csv',
        'format': 'finanzen_zero',
        'enabled': False
    }
}

# ============================================================================
# Bitpanda (Crypto) - Optional
# ============================================================================
# API Key von https://www.bitpanda.com/ → Account → API
BITPANDA_API_KEY = ""  # Dein Bitpanda API Key
BITPANDA_ENABLED = False

# ============================================================================
# Weitere Optionen
# ============================================================================
REVOLUT_API_TOKEN = ""  # Revolut Business API (optional)
REVOLUT_ENABLED = False

# === Häufige Bankleitzahlen (BLZ) - Referenz ===
BANK_CODES_REFERENCE = {
    'C24': '12030000',
    'DKB': '12030000',
    'ING': '50010517',
    'Commerzbank': '50040000',
    'Sparkasse Berlin': '10050000',
    'Postbank': '10010010',
    'Deutsche Bank': '10070000',
}

# ============================================================================
# Sicherheitshinweise
# ============================================================================
# WICHTIG:
# 1. Diese config.py Datei sollte NIEMALS in Git committed werden!
# 2. Die .gitignore ist bereits konfiguriert um config.py auszuschließen
# 3. Für zusätzliche Sicherheit kannst du Umgebungsvariablen nutzen:
#
#    import os
#    CSV_SOURCES = {
#        'c24': {
#            'name': 'C24 Bank',
#            'csv_path': os.getenv('C24_CSV_PATH', 'data/c24.csv'),
#            'format': 'c24',
#            'enabled': True
#        }
#    }

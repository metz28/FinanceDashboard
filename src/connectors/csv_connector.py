# csv_connector.py
"""
CSV-Connector für Bank-Transaktionen (C24 und andere Banken).
Unterstützt verschiedene CSV-Formate und normalisiert sie für die Datenbank.
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import hashlib


class CSVConnector:
    """
    Liest Bank-Transaktionen aus CSV-Dateien.
    Unterstützt verschiedene Bank-Formate und normalisiert sie.
    """

    # Mapping von Bank-CSV-Formaten zu internen Feldnamen
    FIELD_MAPPINGS = {
        'c24': {
            'date': 'Buchungsdatum',
            'amount': 'Betrag',
            'counterpart': 'Zahlungsempfänger',
            'description': 'Verwendungszweck',
            'transaction_type': 'Transaktionstyp',
            'iban': 'IBAN',
            'bic': 'BIC',
            'card_usage': 'Karteneinsatz',
            'category': 'Kategorie',
            'subcategory': 'Unterkategorie',
        },
        # Weitere Bank-Formate können hier hinzugefügt werden
        'generic': {
            'date': 'Datum',
            'amount': 'Betrag',
            'counterpart': 'Empfänger',
            'description': 'Verwendungszweck',
        }
    }

    def __init__(self, bank_id: str, bank_name: str, csv_path: str, bank_format: str = 'c24'):
        """
        Args:
            bank_id: Interne ID (z.B. 'c24', 'dkb')
            bank_name: Anzeigename (z.B. 'C24 Bank')
            csv_path: Pfad zur CSV-Datei oder Ordner mit CSV-Dateien
            bank_format: Format-Identifier für Field-Mapping
        """
        self.bank_id = bank_id
        self.bank_name = bank_name
        self.csv_path = csv_path
        self.bank_format = bank_format
        self.field_mapping = self.FIELD_MAPPINGS.get(bank_format, self.FIELD_MAPPINGS['generic'])

    def fetch_transactions(self, days_back: Optional[int] = None) -> List[Dict]:
        """
        Liest Transaktionen aus CSV-Datei(en).

        Args:
            days_back: Optional - filtert Transaktionen der letzten N Tage

        Returns:
            Liste von standardisierten Transaction-Dicts
        """
        all_transactions = []

        # Unterstützt sowohl einzelne Datei als auch Ordner mit mehreren CSVs
        csv_files = self._get_csv_files()

        for csv_file in csv_files:
            try:
                transactions = self._parse_csv_file(csv_file)
                all_transactions.extend(transactions)
                print(f"  [OK] {len(transactions)} Transaktionen aus {Path(csv_file).name}")
            except Exception as e:
                print(f"  [ERROR] Fehler beim Lesen von {csv_file}: {e}")

        # Optional: Nach Datum filtern
        if days_back:
            cutoff_date = datetime.now().date() - timedelta(days=days_back)
            all_transactions = [
                txn for txn in all_transactions
                if txn['booking_date'] >= cutoff_date
            ]

        return all_transactions

    def _get_csv_files(self) -> List[str]:
        """Gibt Liste von CSV-Dateien zurück (einzelne Datei oder alle in Ordner)"""
        path = Path(self.csv_path)

        if path.is_file():
            return [str(path)]
        elif path.is_dir():
            return [str(f) for f in path.glob('*.csv')]
        else:
            print(f"[WARN] CSV-Pfad existiert nicht: {self.csv_path}")
            return []

    def _parse_csv_file(self, csv_file: str) -> List[Dict]:
        """
        Parst eine einzelne CSV-Datei und normalisiert das Format.

        Returns:
            Liste von standardisierten Transaktionen
        """
        transactions = []

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    normalized = self._normalize_transaction(row)
                    if normalized:
                        transactions.append(normalized)
                except Exception as e:
                    print(f"    [WARN] Fehler beim Parsen einer Zeile: {e}")
                    continue

        return transactions

    def _normalize_transaction(self, row: Dict) -> Optional[Dict]:
        """
        Normalisiert eine CSV-Zeile in standardisiertes Format.

        Returns:
            Dict mit standardisierten Feldern oder None wenn ungültig
        """
        try:
            # Pflichtfelder extrahieren
            date_str = row.get(self.field_mapping['date'], '').strip()
            amount_str = row.get(self.field_mapping['amount'], '').strip()

            # Skip leere Zeilen
            if not date_str or not amount_str:
                return None

            # Datum parsen (C24 Format: DD.MM.YYYY oder YYYY-MM-DD)
            booking_date = self._parse_date(date_str)
            if not booking_date:
                return None

            # Betrag parsen (C24 Format: -123,45 oder 123.45)
            amount = self._parse_amount(amount_str)

            # Gegenpartei und Beschreibung
            counterpart = row.get(self.field_mapping.get('counterpart'), 'Unbekannt').strip()
            description = row.get(self.field_mapping.get('description'), '').strip()

            # Optionale Felder
            card_usage = row.get(self.field_mapping.get('card_usage', ''), '').strip()
            if card_usage:
                description = f"{description} | Karte: {card_usage}".strip()

            # Generiere eindeutige ID
            transaction_id = self._generate_transaction_id(booking_date, amount, counterpart, description)

            return {
                'id': transaction_id,
                'booking_date': booking_date,
                'amount': amount,
                'currency': 'EUR',  # C24 ist immer EUR
                'counterpart': counterpart or 'Unbekannt',
                'description': description,
                'bank_name': self.bank_name,
                'account_iban': row.get(self.field_mapping.get('iban'), 'N/A')
            }

        except Exception as e:
            print(f"    [WARN] Normalisierung fehlgeschlagen: {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """Parst verschiedene Datumsformate"""
        date_formats = [
            '%d.%m.%Y',     # 01.01.2024
            '%Y-%m-%d',     # 2024-01-01
            '%d/%m/%Y',     # 01/01/2024
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        print(f"    [WARN] Ungültiges Datumsformat: {date_str}")
        return None

    def _parse_amount(self, amount_str: str) -> float:
        """
        Parst Beträge in verschiedenen Formaten.

        Beispiele:
            -123,45 -> -123.45
            1.234,56 -> 1234.56
            -123.45 -> -123.45
        """
        # Entferne Währungssymbole und Whitespace
        amount_str = amount_str.replace('€', '').replace('EUR', '').strip()

        # Deutsche Notation: 1.234,56 -> 1234.56
        if ',' in amount_str and '.' in amount_str:
            amount_str = amount_str.replace('.', '').replace(',', '.')
        # Nur Komma: 123,45 -> 123.45
        elif ',' in amount_str:
            amount_str = amount_str.replace(',', '.')

        return float(amount_str)

    def _generate_transaction_id(self, date, amount, counterpart, description) -> str:
        """Generiert eindeutige Transaction-ID aus Hash"""
        unique_string = f"{self.bank_id}_{date}_{amount}_{counterpart}_{description[:50]}"
        return hashlib.md5(unique_string.encode()).hexdigest()


class CSVBankManager:
    """
    Verwaltet mehrere CSV-basierte Banken.
    Analog zum FinTS BankManager.
    """

    def __init__(self, csv_sources: dict):
        """
        Args:
            csv_sources: Dict aus config.py mit CSV-Konfigurationen
        """
        self.banks = {}

        for bank_id, config in csv_sources.items():
            if config.get('enabled', False):
                try:
                    self.banks[bank_id] = CSVConnector(
                        bank_id=bank_id,
                        bank_name=config['name'],
                        csv_path=config['csv_path'],
                        bank_format=config.get('format', 'c24')
                    )
                    print(f"[CSV] Loaded: {config['name']}")
                except Exception as e:
                    print(f"[CSV] Failed to load {config.get('name', bank_id)}: {e}")

    def fetch_all_transactions(self, days_back: Optional[int] = None) -> List[Dict]:
        """
        Liest Transaktionen aus allen konfigurierten CSV-Quellen.

        Args:
            days_back: Optional - Tage zurück

        Returns:
            Kombinierte Liste aller Transaktionen
        """
        all_transactions = []

        for bank_id, connector in self.banks.items():
            try:
                print(f"Lese CSV-Transaktionen von {connector.bank_name}...")
                txns = connector.fetch_transactions(days_back=days_back)
                all_transactions.extend(txns)
            except Exception as e:
                print(f"  [ERROR] {e}")

        return all_transactions


# CLI Test
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config import CSV_SOURCES

    print("=== CSV Bank Manager Test ===\n")

    if not CSV_SOURCES:
        print("[WARN] Keine CSV-Quellen in config.py konfiguriert!")
        print("\nFüge folgendes zu config.py hinzu:")
        print("""
CSV_SOURCES = {
    'c24': {
        'name': 'C24 Bank',
        'csv_path': 'pfad/zu/c24_transaktionen.csv',
        'format': 'c24',
        'enabled': True
    }
}
        """)
        exit(1)

    manager = CSVBankManager(CSV_SOURCES)

    if not manager.banks:
        print("[ERROR] Keine CSV-Banken geladen!")
        exit(1)

    print(f"\n{len(manager.banks)} CSV-Quelle(n) geladen\n")

    # Transaktionen laden
    transactions = manager.fetch_all_transactions()

    print(f"\n=== Gesamt: {len(transactions)} Transaktionen ===\n")

    if transactions:
        print("Erste 5 Transaktionen:")
        for txn in sorted(transactions, key=lambda x: x['booking_date'], reverse=True)[:5]:
            print(f"  {txn['booking_date']} | {txn['bank_name']:15} | {txn['amount']:>8.2f} EUR | {txn['counterpart'][:30]}")

# broker_connector.py
"""
Broker-Connector für Wertpapier-Orders (Finanzen Zero, Trade Republic, etc.).
Liest Order-CSV-Dateien und normalisiert sie für die Datenbank.
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import hashlib


class BrokerConnector:
    """
    Liest Wertpapier-Orders aus CSV-Dateien (Broker wie Finanzen Zero).
    Unterstützt verschiedene Broker-Formate.
    """

    # Mapping von Broker-CSV-Formaten zu internen Feldnamen
    FIELD_MAPPINGS = {
        'finanzen_zero': {
            'name': 'Name',
            'isin': 'ISIN',
            'wkn': 'WKN',
            'quantity': 'Anzahl',
            'quantity_cancelled': 'Anzahl storniert',
            'status': 'Status',
            'order_type': 'Orderart',
            'limit': 'Limit',
            'stop': 'Stop',
            'created_date': 'Erstellt Datum',
            'created_time': 'Erstellt Zeit',
            'valid_until': 'Gültig bis',
            'direction': 'Richtung',
            'value': 'Wert',
            'value_cancelled': 'Wert storniert',
            'execution_date': 'Ausführung Datum',
            'execution_time': 'Ausführung Zeit',
            'execution_price': 'Ausführung Kurs',
            'quantity_executed': 'Anzahl ausgeführt',
            'quantity_open': 'Anzahl offen',
            'cancelled_date': 'Gestrichen Datum',
            'cancelled_time': 'Gestrichen Zeit',
        },
        # Weitere Broker-Formate können hier hinzugefügt werden
        'generic': {
            'name': 'Name',
            'isin': 'ISIN',
            'quantity': 'Anzahl',
            'direction': 'Richtung',
            'value': 'Wert',
            'execution_date': 'Datum',
        }
    }

    def __init__(self, broker_id: str, broker_name: str, csv_path: str, broker_format: str = 'finanzen_zero'):
        """
        Args:
            broker_id: Interne ID (z.B. 'finanzen_zero', 'trade_republic')
            broker_name: Anzeigename (z.B. 'Finanzen Zero')
            csv_path: Pfad zur CSV-Datei oder Ordner mit CSV-Dateien
            broker_format: Format-Identifier für Field-Mapping
        """
        self.broker_id = broker_id
        self.broker_name = broker_name
        self.csv_path = csv_path
        self.broker_format = broker_format
        self.field_mapping = self.FIELD_MAPPINGS.get(broker_format, self.FIELD_MAPPINGS['generic'])

    def fetch_orders(self, days_back: Optional[int] = None) -> List[Dict]:
        """
        Liest Orders aus CSV-Datei(en).

        Args:
            days_back: Optional - filtert Orders der letzten N Tage

        Returns:
            Liste von standardisierten Order-Dicts
        """
        all_orders = []

        # Unterstützt sowohl einzelne Datei als auch Ordner mit mehreren CSVs
        csv_files = self._get_csv_files()

        for csv_file in csv_files:
            try:
                orders = self._parse_csv_file(csv_file)
                all_orders.extend(orders)
                print(f"  [OK] {len(orders)} Orders aus {Path(csv_file).name}")
            except Exception as e:
                print(f"  [ERROR] Fehler beim Lesen von {csv_file}: {e}")

        # Optional: Nach Datum filtern
        if days_back:
            from datetime import timedelta
            cutoff_date = datetime.now().date() - timedelta(days=days_back)
            all_orders = [
                order for order in all_orders
                if order['execution_date'] and order['execution_date'] >= cutoff_date
            ]

        return all_orders

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
            Liste von standardisierten Orders
        """
        orders = []

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            # Finanzen Zero nutzt Semikolon als Delimiter
            reader = csv.DictReader(f, delimiter=';')

            for row in reader:
                try:
                    normalized = self._normalize_order(row)
                    if normalized:
                        orders.append(normalized)
                except Exception as e:
                    print(f"    [WARN] Fehler beim Parsen einer Zeile: {e}")
                    continue

        return orders

    def _normalize_order(self, row: Dict) -> Optional[Dict]:
        """
        Normalisiert eine CSV-Zeile in standardisiertes Format.

        Returns:
            Dict mit standardisierten Feldern oder None wenn ungültig
        """
        try:
            # Pflichtfelder extrahieren
            name = row.get(self.field_mapping.get('name', ''), '').strip()
            isin = row.get(self.field_mapping.get('isin', ''), '').strip()
            direction = row.get(self.field_mapping.get('direction', ''), '').strip()

            # Skip leere Zeilen oder Zeilen ohne ISIN
            if not isin or not name:
                return None

            # Datum parsen
            execution_date_str = row.get(self.field_mapping.get('execution_date', ''), '').strip()
            execution_date = self._parse_date(execution_date_str) if execution_date_str else None

            # Anzahl und Werte parsen
            quantity = self._parse_number(row.get(self.field_mapping.get('quantity', ''), '0'))
            quantity_executed = self._parse_number(row.get(self.field_mapping.get('quantity_executed', ''), '0'))
            value = self._parse_number(row.get(self.field_mapping.get('value', ''), '0'))
            execution_price = self._parse_number(row.get(self.field_mapping.get('execution_price', ''), '0'))

            # Status
            status = row.get(self.field_mapping.get('status', ''), '').strip()
            order_type = row.get(self.field_mapping.get('order_type', ''), '').strip()

            # Erstell-Datum parsen
            created_date_str = row.get(self.field_mapping.get('created_date', ''), '').strip()
            created_date = self._parse_date(created_date_str) if created_date_str else None

            # Generiere eindeutige ID
            order_id = self._generate_order_id(isin, created_date, quantity, direction)

            return {
                'id': order_id,
                'broker_name': self.broker_name,
                'security_name': name,
                'isin': isin,
                'wkn': row.get(self.field_mapping.get('wkn', ''), '').strip(),
                'direction': direction,  # Kauf/Verkauf
                'quantity': quantity,
                'quantity_executed': quantity_executed,
                'order_type': order_type,  # Market, Limit, etc.
                'status': status,
                'value': value,
                'execution_price': execution_price,
                'execution_date': execution_date,
                'created_date': created_date,
                'currency': 'EUR',  # Default EUR
            }

        except Exception as e:
            print(f"    [WARN] Normalisierung fehlgeschlagen: {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """Parst verschiedene Datumsformate"""
        if not date_str or date_str.strip() == '':
            return None

        date_formats = [
            '%d.%m.%Y',     # 01.01.2024
            '%Y-%m-%d',     # 2024-01-01
            '%d/%m/%Y',     # 01/01/2024
            '%d.%m.%y',     # 01.01.24
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        print(f"    [WARN] Ungültiges Datumsformat: {date_str}")
        return None

    def _parse_number(self, number_str: str) -> float:
        """
        Parst Zahlen in verschiedenen Formaten.

        Beispiele:
            123,45 -> 123.45
            1.234,56 -> 1234.56
            123.45 -> 123.45
        """
        if not number_str or number_str.strip() == '':
            return 0.0

        # Entferne Währungssymbole und Whitespace
        number_str = number_str.replace('€', '').replace('EUR', '').strip()

        # Deutsche Notation: 1.234,56 -> 1234.56
        if ',' in number_str and '.' in number_str:
            number_str = number_str.replace('.', '').replace(',', '.')
        # Nur Komma: 123,45 -> 123.45
        elif ',' in number_str:
            number_str = number_str.replace(',', '.')

        try:
            return float(number_str)
        except ValueError:
            return 0.0

    def _generate_order_id(self, isin, date, quantity, direction) -> str:
        """Generiert eindeutige Order-ID aus Hash"""
        unique_string = f"{self.broker_id}_{isin}_{date}_{quantity}_{direction}"
        return hashlib.md5(unique_string.encode()).hexdigest()


class BrokerManager:
    """
    Verwaltet mehrere Broker-Connectoren.
    Analog zum CSV BankManager.
    """

    def __init__(self, broker_sources: dict):
        """
        Args:
            broker_sources: Dict aus config.py mit Broker-Konfigurationen
        """
        self.brokers = {}

        for broker_id, config in broker_sources.items():
            if config.get('enabled', False):
                try:
                    self.brokers[broker_id] = BrokerConnector(
                        broker_id=broker_id,
                        broker_name=config['name'],
                        csv_path=config['csv_path'],
                        broker_format=config.get('format', 'finanzen_zero')
                    )
                    print(f"[BROKER] Loaded: {config['name']}")
                except Exception as e:
                    print(f"[BROKER] Failed to load {config.get('name', broker_id)}: {e}")

    def fetch_all_orders(self, days_back: Optional[int] = None) -> List[Dict]:
        """
        Liest Orders aus allen konfigurierten Broker-Quellen.

        Args:
            days_back: Optional - Tage zurück

        Returns:
            Kombinierte Liste aller Orders
        """
        all_orders = []

        for broker_id, connector in self.brokers.items():
            try:
                print(f"Lese Orders von {connector.broker_name}...")
                orders = connector.fetch_orders(days_back=days_back)
                all_orders.extend(orders)
            except Exception as e:
                print(f"  [ERROR] {e}")

        return all_orders


# CLI Test
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config import BROKER_SOURCES

    print("=== Broker Manager Test ===\n")

    if not BROKER_SOURCES:
        print("[WARN] Keine Broker-Quellen in config.py konfiguriert!")
        print("\nFüge folgendes zu config.py hinzu:")
        print("""
BROKER_SOURCES = {
    'finanzen_zero': {
        'name': 'Finanzen Zero',
        'csv_path': 'data/finanzen_zero_orders.csv',
        'format': 'finanzen_zero',
        'enabled': True
    }
}
        """)
        exit(1)

    manager = BrokerManager(BROKER_SOURCES)

    if not manager.brokers:
        print("[ERROR] Keine Broker geladen!")
        exit(1)

    print(f"\n{len(manager.brokers)} Broker-Quelle(n) geladen\n")

    # Orders laden
    orders = manager.fetch_all_orders()

    print(f"\n=== Gesamt: {len(orders)} Orders ===\n")

    if orders:
        print("Erste 5 Orders:")
        sorted_orders = sorted([o for o in orders if o['execution_date']],
                              key=lambda x: x['execution_date'],
                              reverse=True)[:5]

        for order in sorted_orders:
            print(f"  {order['execution_date']} | {order['direction']:8} | {order['quantity_executed']:>6.0f}x {order['security_name'][:20]:20} @ {order['execution_price']:>8.2f} EUR")

# fints_connector.py
"""
Direct bank connection using FinTS/HBCI protocol.
No third-party API needed - connects directly to German banks.
"""

from fints.client import FinTS3PinTanClient
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.WARNING)


class FinTSConnector:
    """Handles FinTS connections for German banks"""

    def __init__(self, bank_id: str, bank_config: dict):
        """
        Initialize FinTS connection.

        Args:
            bank_id: Internal identifier (e.g., 'c24', 'dkb')
            bank_config: Dict with keys: 'name', 'blz', 'username', 'pin'
        """
        self.bank_id = bank_id
        self.bank_name = bank_config['name']
        self.blz = bank_config['blz']
        self.username = bank_config['username']
        self.pin = bank_config['pin']
        self.endpoint = bank_config.get('endpoint')  # Optional FinTS server URL
        self.product_id = bank_config.get('product_id', 'FinanceDashboard')
        self.client = None

    def connect(self):
        """Establish connection to bank"""
        if not self.client:
            self.client = FinTS3PinTanClient(
                self.blz,
                self.username,
                self.pin,
                self.endpoint,
                product_id=self.product_id
            )
        return self.client

    def get_accounts(self):
        """Fetch all accounts (checking, savings, etc.)"""
        if not self.client:
            self.connect()
        return self.client.get_sepa_accounts()

    def fetch_transactions(self, days_back: int = 90) -> List[Dict]:
        """
        Fetch transactions from all accounts.

        Args:
            days_back: Number of days of history to fetch

        Returns:
            List of transaction dicts in standardized format
        """
        if not self.client:
            self.connect()

        start_date = datetime.now().date() - timedelta(days=days_back)
        end_date = datetime.now().date()

        all_transactions = []
        accounts = self.get_accounts()

        for account in accounts:
            try:
                transactions = self.client.get_transactions(
                    account,
                    start_date=start_date,
                    end_date=end_date
                )

                for txn in transactions:
                    # Standardize transaction format for your warehouse
                    normalized = {
                        'id': self._generate_transaction_id(txn, account),
                        'booking_date': txn.data.get('date') or txn.data.get('booking_date'),
                        'amount': float(txn.data.get('amount').amount),
                        'currency': txn.data.get('amount').currency,
                        'counterpart': txn.data.get('applicant_name', 'Unknown'),
                        'description': txn.data.get('purpose', ''),
                        'bank_name': self.bank_name,
                        'account_iban': account.iban
                    }
                    all_transactions.append(normalized)

            except Exception as e:
                logging.error(f"[{self.bank_name}] Error fetching transactions for {account.iban}: {e}")

        return all_transactions

    def get_balances(self) -> Dict[str, float]:
        """
        Get current balances for all accounts.

        Returns:
            Dict mapping IBAN -> balance (in EUR)
        """
        if not self.client:
            self.connect()

        accounts = self.get_accounts()
        balances = {}

        for account in accounts:
            try:
                balance = self.client.get_balance(account)
                balances[account.iban] = float(balance.amount)
            except Exception as e:
                logging.error(f"[{self.bank_name}] Error fetching balance for {account.iban}: {e}")

        return balances

    def _generate_transaction_id(self, txn, account) -> str:
        """Generate unique transaction ID from transaction data"""
        date = txn.data.get('date') or txn.data.get('booking_date')
        amount = txn.data.get('amount').amount
        purpose = txn.data.get('purpose', '')[:50]
        unique_string = f"{account.iban}_{date}_{amount}_{purpose}"
        return str(abs(hash(unique_string)))


class BankManager:
    """
    Manages multiple bank connections.
    Automatically loads enabled banks from config.
    """

    def __init__(self, banks_config: dict):
        """
        Args:
            banks_config: FINTS_BANKS dict from config.py
        """
        self.banks = {}

        for bank_id, config in banks_config.items():
            if config.get('enabled', False):
                try:
                    self.banks[bank_id] = FinTSConnector(bank_id, config)
                    logging.info(f"Loaded bank: {config['name']}")
                except Exception as e:
                    logging.error(f"Failed to initialize {config.get('name', bank_id)}: {e}")

    def fetch_all_transactions(self, days_back: int = 90) -> List[Dict]:
        """
        Fetch transactions from all enabled banks.

        Args:
            days_back: Days of history to fetch

        Returns:
            Combined list of all transactions
        """
        all_transactions = []

        for bank_id, connector in self.banks.items():
            try:
                print(f"Fetching transactions from {connector.bank_name}...")
                txns = connector.fetch_transactions(days_back=days_back)
                all_transactions.extend(txns)
                print(f"  [OK] {len(txns)} transactions")
            except Exception as e:
                print(f"  [ERROR] {e}")
                logging.error(f"Failed to fetch from {bank_id}: {e}")

        return all_transactions

    def get_all_balances(self) -> Dict[str, Dict[str, float]]:
        """
        Get balances from all enabled banks.

        Returns:
            Dict mapping bank_name -> {iban: balance}
        """
        all_balances = {}

        for bank_id, connector in self.banks.items():
            try:
                balances = connector.get_balances()
                all_balances[connector.bank_name] = balances
            except Exception as e:
                logging.error(f"Failed to fetch balances from {bank_id}: {e}")

        return all_balances

    def get_bank(self, bank_id: str) -> Optional[FinTSConnector]:
        """Get specific bank connector by ID"""
        return self.banks.get(bank_id)


# CLI usage example
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config import FINTS_BANKS

    print("=== FinTS Bank Manager ===\n")

    # Initialize manager with all enabled banks
    manager = BankManager(FINTS_BANKS)

    if not manager.banks:
        print("No banks configured or enabled!")
        print("Edit config.py and set enabled=True for your banks.")
        exit(1)

    print(f"Loaded {len(manager.banks)} bank(s)\n")

    # Show accounts for each bank
    print("=== Accounts ===")
    for bank_id, connector in manager.banks.items():
        print(f"\n{connector.bank_name}:")
        try:
            accounts = connector.get_accounts()
            for acc in accounts:
                print(f"  {acc.iban} ({acc.type})")
        except Exception as e:
            print(f"  Error: {e}")

    # Show balances
    print("\n=== Balances ===")
    all_balances = manager.get_all_balances()
    for bank_name, balances in all_balances.items():
        print(f"\n{bank_name}:")
        for iban, balance in balances.items():
            print(f"  {iban}: {balance:>10.2f} EUR")

    # Fetch recent transactions
    print("\n=== Recent Transactions (last 30 days) ===")
    transactions = manager.fetch_all_transactions(days_back=30)

    print(f"\nTotal: {len(transactions)} transactions")

    if transactions:
        print("\nMost recent 5:")
        for txn in sorted(transactions, key=lambda x: x['booking_date'], reverse=True)[:5]:
            print(f"  {txn['booking_date']} | {txn['bank_name']:15} | {txn['amount']:>8.2f} EUR | {txn['counterpart'][:30]}")

# FinanceDashboard Setup Guide

## Overview
This project automatically fetches financial data from various sources and stores it in a central DuckDB database.

**Key features:**
- Direct bank connection via FinTS (no third-party API needed)
- Supports all major German banks (Sparkasse, DKB, ING, C24, etc.)
- Bitpanda crypto integration
- Local DuckDB data warehouse

---

## 1. Install Dependencies

```bash
pip install fints duckdb pandas requests
```

---

## 2. Configure Banks (FinTS)

### What is FinTS?
FinTS (Financial Transaction Services) is a standardized protocol that lets you connect **directly** to your German bank - no third-party service needed. Most German banks support it.

### Step 1: Find your bank's BLZ (Bankleitzahl)

Common bank codes are in `config.py` under `BANK_CODES_REFERENCE`. Some examples:

| Bank | BLZ |
|------|-----|
| C24 | 12030000 |
| DKB | 12030000 |
| ING | 50010517 |
| Commerzbank | 50040000 |
| Sparkasse Berlin | 10050000 |

You can find any BLZ at: https://www.sparkasse.de/service/bankleitzahlen.html

### Step 2: Edit config.py

```python
FINTS_BANKS = {
    'c24': {
        'name': 'C24 Bank',
        'blz': '12030000',              # Your bank's BLZ
        'username': 'your_username',    # Your online banking username
        'pin': 'your_pin',              # Your online banking PIN
        'enabled': True                 # Set to True to activate
    },
    # Add more banks:
    'dkb': {
        'name': 'DKB',
        'blz': '12030000',
        'username': 'dkb_user',
        'pin': 'dkb_pin',
        'enabled': True
    },
}
```

### Step 3: Test Connection

```bash
python fints_connector.py
```

This will:
- Connect to all enabled banks
- Show your accounts and IBANs
- Display current balances
- Fetch recent transactions

**Note:** First connection may take 10-20 seconds while establishing secure channel.

### Troubleshooting FinTS

**"Invalid credentials"**
- Double-check username and PIN
- Some banks use separate FinTS PINs - check your bank's settings

**"Bank not supported"**
- Not all banks support FinTS (e.g., N26 has limited support)
- Check your bank's documentation for "FinTS" or "HBCI" support

**"Connection timeout"**
- Some banks rate-limit FinTS connections
- Wait a few minutes and try again

**"TAN required"**
- Some banks require TAN (Transaction Authentication Number) for first setup
- Run the script and follow the TAN prompt

---

## 3. Bitpanda (Optional - Crypto)

### Get API Key

1. Go to https://www.bitpanda.com/
2. Login → Account → API
3. Create new API key (read-only permissions)

### Update config.py

```python
BITPANDA_API_KEY = "your_api_key_here"
BITPANDA_ENABLED = True
```

---

## 4. Initialize Database

```bash
python warehouse.py
```

This creates `finance.duckdb` with tables:
- `bank_transactions` - all bank transactions
- `bitpanda_wallets` - crypto holdings
- `bitpanda_trades` - crypto trades
- `portfolio_snapshots` - historical portfolio value

---

## 5. Run ETL Pipeline

```bash
python etl_pipeline.py
```

Expected output:
```
=== ETL Pipeline Start ===
Fetching transactions from C24 Bank...
  ✓ 127 transactions
Fetching transactions from DKB...
  ✓ 89 transactions
✓ Bitpanda: 45 trades, 3 wallets
=== Pipeline Complete ===
```

---

## 6. Query Your Data

### Python Shell
```bash
python
```

```python
import duckdb
con = duckdb.connect("finance.duckdb")

# Show recent transactions
con.execute("""
    SELECT booking_date, bank_name, amount, counterpart
    FROM bank_transactions
    ORDER BY booking_date DESC
    LIMIT 10
""").df()

# Monthly spending by bank
con.execute("""
    SELECT
        bank_name,
        DATE_TRUNC('month', booking_date) as month,
        SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses,
        SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income
    FROM bank_transactions
    GROUP BY bank_name, month
    ORDER BY month DESC
""").df()

# Current balances (calculate from transactions)
con.execute("""
    SELECT
        bank_name,
        COUNT(*) as transaction_count,
        SUM(amount) as balance
    FROM bank_transactions
    GROUP BY bank_name
""").df()
```

### Useful Queries

**Top 10 expenses this month:**
```sql
SELECT
    booking_date,
    counterpart,
    amount,
    bank_name
FROM bank_transactions
WHERE amount < 0
  AND booking_date >= DATE_TRUNC('month', CURRENT_DATE)
ORDER BY amount ASC
LIMIT 10;
```

**Spending by category (needs categorization logic):**
```sql
SELECT
    CASE
        WHEN counterpart LIKE '%REWE%' OR counterpart LIKE '%EDEKA%' THEN 'Groceries'
        WHEN counterpart LIKE '%AMAZON%' THEN 'Shopping'
        ELSE 'Other'
    END as category,
    SUM(amount) as total
FROM bank_transactions
WHERE amount < 0
GROUP BY category
ORDER BY total;
```

**Bitpanda portfolio:**
```sql
SELECT
    wallet_name,
    asset_symbol,
    balance,
    balance_eur
FROM bitpanda_wallets
ORDER BY balance_eur DESC;
```

---

## 7. Automation

### Windows Task Scheduler

Run daily at 8:00 AM:
```powershell
schtasks /create /tn "FinanceETL" /tr "python C:\Users\maxis\Desktop\FinanceDashboard\etl_pipeline.py" /sc daily /st 08:00
```

### Linux/Mac Cron

```bash
crontab -e
```

Add line:
```
0 8 * * * cd /path/to/FinanceDashboard && python etl_pipeline.py
```

---

## 8. Security Best Practices

### Never commit credentials

The `.gitignore` already excludes `config.py`, but verify:

```bash
git status
# config.py should NOT appear
```

### Use environment variables (optional)

For added security, use environment variables instead of hardcoding:

```python
# config.py
import os

FINTS_BANKS = {
    'c24': {
        'name': 'C24 Bank',
        'blz': '12030000',
        'username': os.getenv('C24_USERNAME'),
        'pin': os.getenv('C24_PIN'),
        'enabled': True
    }
}
```

Then set in your shell:
```bash
export C24_USERNAME="your_username"
export C24_PIN="your_pin"
```

### Database encryption (optional)

For sensitive data, consider encrypting the DuckDB file at rest using OS-level encryption (BitLocker on Windows, LUKS on Linux, FileVault on Mac).

---

## Adding More Banks

1. Find your bank's BLZ code
2. Add entry to `FINTS_BANKS` in `config.py`
3. Set `enabled: True`
4. Run `python fints_connector.py` to test
5. Run `python etl_pipeline.py` to sync

**Example:**
```python
'ing': {
    'name': 'ING',
    'blz': '50010517',
    'username': 'your_ing_username',
    'pin': 'your_ing_pin',
    'enabled': True
},
```

---

## Revolut

Revolut doesn't support FinTS. Options:

1. **Revolut Business API** - requires business account
2. **CSV Export** - manual export from app, then import to database
3. **Wait for Open Banking** - Revolut is rolling out PSD2 access

For now, CSV export is the most practical for personal use.

---

## Need Help?

Common issues:
- **"No banks configured"** - Set `enabled: True` in config.py
- **"Invalid PIN"** - Check if your bank uses a separate FinTS PIN
- **"TAN required"** - Follow the prompt in your terminal
- **"Connection refused"** - Bank may be blocking FinTS temporarily

Check the Python logs for detailed error messages.

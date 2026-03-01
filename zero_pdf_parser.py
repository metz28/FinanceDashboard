# zero_pdf_parser.py
# Nutze "portfolio-report" CLI tool: https://github.com/buehner/portfolio-report
# Oder manuelles CSV mit diesem Schema befüllen:

import pandas as pd

def load_zero_manual_csv(path: str) -> pd.DataFrame:
    """
    Erwartetes CSV-Format:
    date, type, isin, name, shares, price, total, currency
    2024-03-15, BUY, DE0005140008, Deutsche Bank, 10, 12.50, 125.00, EUR
    """
    return pd.read_csv(path, parse_dates=["date"])
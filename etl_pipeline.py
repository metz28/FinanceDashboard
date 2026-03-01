# etl_pipeline.py
from bitpanda_connector import fetch_all_trades, store_bitpanda_trades

if __name__ == "__main__":
    store_bitpanda_trades()
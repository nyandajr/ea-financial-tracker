"""
fetch_data.py
Fetches exchange rates and crypto prices, saves to CSV in /data
APIs used:
  - Frankfurter (free, no key) → TZS/KES/UGX vs USD/EUR
  - CoinGecko   (free, no key) → BTC/ETH/USDT prices
"""

import requests
import pandas as pd
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

FX_FILE     = os.path.join(DATA_DIR, 'exchange_rates.csv')
CRYPTO_FILE = os.path.join(DATA_DIR, 'crypto_prices.csv')

# ── Exchange Rates ─────────────────────────────────────────────
def fetch_exchange_rates():
    """Fetch USD → TZS, KES, UGX, EUR, GBP from ExchangeRate-API (free, no key)"""
    try:
        url = 'https://open.er-api.com/v6/latest/USD'
        r = requests.get(url, timeout=10)
        data = r.json()
        rates = data.get('rates', {})
        row = {
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'USD_TZS': rates.get('TZS', None),
            'USD_KES': rates.get('KES', None),
            'USD_UGX': rates.get('UGX', None),
            'USD_EUR': rates.get('EUR', None),
            'USD_GBP': rates.get('GBP', None),
        }
        df_new = pd.DataFrame([row])
        if os.path.exists(FX_FILE):
            df = pd.read_csv(FX_FILE)
            df = pd.concat([df, df_new], ignore_index=True).drop_duplicates(subset='timestamp')
        else:
            df = df_new
        # Keep last 30 days of hourly data (~720 rows)
        df = df.tail(720)
        df.to_csv(FX_FILE, index=False)
        print(f"✅ Exchange rates saved: USD/TZS={row['USD_TZS']}, USD/KES={row['USD_KES']}")
        return row
    except Exception as e:
        print(f"❌ Exchange rate fetch failed: {e}")
        return None

# ── Crypto Prices ──────────────────────────────────────────────
def fetch_crypto_prices():
    """Fetch BTC, ETH, USDT prices in USD from CoinGecko"""
    try:
        url = 'https://api.coingecko.com/api/v3/simple/price'
        params = {
            'ids': 'bitcoin,ethereum,tether,binancecoin',
            'vs_currencies': 'usd,kes',
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        row = {
            'timestamp':    datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'BTC_USD':      data.get('bitcoin',     {}).get('usd',  None),
            'BTC_KES':      data.get('bitcoin',     {}).get('kes',  None),
            'ETH_USD':      data.get('ethereum',    {}).get('usd',  None),
            'ETH_KES':      data.get('ethereum',    {}).get('kes',  None),
            'USDT_USD':     data.get('tether',      {}).get('usd',  None),
            'BNB_USD':      data.get('binancecoin', {}).get('usd',  None),
        }
        df_new = pd.DataFrame([row])
        if os.path.exists(CRYPTO_FILE):
            df = pd.read_csv(CRYPTO_FILE)
            df = pd.concat([df, df_new], ignore_index=True).drop_duplicates(subset='timestamp')
        else:
            df = df_new
        df = df.tail(720)
        df.to_csv(CRYPTO_FILE, index=False)
        print(f"✅ Crypto prices saved: BTC=${row['BTC_USD']:,}")
        return row
    except Exception as e:
        print(f"❌ Crypto fetch failed: {e}")
        return None

if __name__ == '__main__':
    fetch_exchange_rates()
    fetch_crypto_prices()

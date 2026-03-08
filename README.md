# 📊 East Africa Financial Tracker

Real-time exchange rates and crypto price tracker with **ML predictions**, built with Streamlit. Auto-updates and commits to GitHub **every hour** 🔁

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?logo=streamlit)
![ML](https://img.shields.io/badge/ML-scikit--learn-orange?logo=scikitlearn)
![Auto Commits](https://img.shields.io/badge/Auto%20Commits-Hourly-green)

---

## ✨ Features
- 💱 **Exchange Rates** — USD → TZS, KES, UGX, EUR (hourly)
- 🪙 **Crypto Prices** — BTC, ETH, BNB in USD/KES
- 🤖 **ML Predictions** — Linear Regression, next 24h forecast
- 📈 **Interactive Charts** — Plotly time series
- 🔁 **Auto-commits** every hour via cron job

## 🏗️ Project Structure
```
ea-financial-tracker/
├── src/
│   ├── app.py          # Streamlit dashboard
│   ├── fetch_data.py   # API data fetcher
│   └── predict.py      # ML prediction engine
├── data/
│   ├── exchange_rates.csv   # Historical FX data (auto-updated)
│   ├── crypto_prices.csv    # Historical crypto data (auto-updated)
│   └── predictions.json     # Latest ML predictions
├── auto_update.sh      # Hourly cron script
└── requirements.txt
```

## 🛠️ Tech Stack
| Tool | Purpose |
|------|---------|
| Streamlit | Web dashboard |
| scikit-learn | ML predictions (Linear Regression) |
| Plotly | Interactive charts |
| Frankfurter API | Free FX rates (no key needed) |
| CoinGecko API | Free crypto prices (no key needed) |

## 🚀 Setup
```bash
git clone https://github.com/nyandajr/ea-financial-tracker.git
cd ea-financial-tracker
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/app.py
```

## 👤 Author
**Freddy Nyanda** — [@nyandajr](https://github.com/nyandajr)

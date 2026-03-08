"""
predict.py
ML predictions using Linear Regression + trend analysis
Predicts next 24hrs for exchange rates and crypto prices
Includes full evaluation metrics: MAE, RMSE, MAPE, R²
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA_DIR  = os.path.join(os.path.dirname(__file__), '..', 'data')
PRED_FILE = os.path.join(DATA_DIR, 'predictions.json')

def make_features(series, window=6):
    """Create lag features for ML model"""
    X, y = [], []
    for i in range(window, len(series)):
        X.append(series[i-window:i])
        y.append(series[i])
    return np.array(X), np.array(y)

def evaluate_metrics(y_true, y_pred):
    """Calculate MAE, RMSE, MAPE and R² on original scale values"""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    mae    = mean_absolute_error(y_true, y_pred)
    rmse   = np.sqrt(mean_squared_error(y_true, y_pred))
    # MAPE — avoid divide-by-zero
    mask   = y_true != 0
    mape   = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    r2     = r2_score(y_true, y_pred)
    return {
        'MAE':  round(mae, 6),
        'RMSE': round(rmse, 6),
        'MAPE': round(mape, 4),   # in %
        'R2':   round(r2, 4),
    }

def predict_next_24h(series, label, window=6, test_ratio=0.2):
    """
    Train Linear Regression on lag features with an 80/20 train-test split.
    Returns (predictions_next_24h, change_pct, metrics_dict)
    """
    try:
        values = series.dropna().values.astype(float)
        if len(values) < window + 5:
            return None, None, None

        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(values.reshape(-1, 1)).flatten()

        X, y = make_features(scaled, window)
        if len(X) < 5:
            return None, None, None

        # ── Train / Test split ─────────────────────────────────
        split  = max(1, int(len(X) * (1 - test_ratio)))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        model = LinearRegression()
        model.fit(X_train, y_train)

        # ── Evaluation on test set ─────────────────────────────
        metrics = None
        if len(X_test) > 0:
            y_pred_scaled = model.predict(X_test)
            # Inverse-scale both arrays for human-readable metrics
            y_test_real = scaler.inverse_transform(y_test.reshape(-1,1)).flatten()
            y_pred_real = scaler.inverse_transform(y_pred_scaled.reshape(-1,1)).flatten()
            metrics = evaluate_metrics(y_test_real, y_pred_real)

        # ── Predict next 24 hours step by step ────────────────
        current = list(scaled[-window:])
        predictions = []
        for _ in range(24):
            pred = model.predict([current[-window:]])[0]
            predictions.append(pred)
            current.append(pred)

        predictions_real = scaler.inverse_transform(
            np.array(predictions).reshape(-1, 1)
        ).flatten().tolist()

        current_val    = float(values[-1])
        predicted_next = predictions_real[0]
        change_pct     = ((predicted_next - current_val) / current_val) * 100

        return predictions_real, round(change_pct, 3), metrics

    except Exception as e:
        print(f"  Prediction failed for {label}: {e}")
        return None, None, None

def run_predictions():
    """Run ML predictions on all available data and save with evaluation metrics"""
    results = {
        'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        'exchange_rates': {},
        'crypto': {}
    }

    # ── Exchange rate predictions ──
    fx_file = os.path.join(DATA_DIR, 'exchange_rates.csv')
    if os.path.exists(fx_file):
        df = pd.read_csv(fx_file)
        for col in ['USD_TZS', 'USD_KES', 'USD_UGX', 'USD_EUR']:
            if col in df.columns and df[col].notna().sum() >= 10:
                preds, change, metrics = predict_next_24h(df[col], col)
                current = float(df[col].dropna().iloc[-1])
                results['exchange_rates'][col] = {
                    'current':     round(current, 4),
                    'next_1h':     round(preds[0], 4) if preds else current,
                    'next_24h':    round(preds[-1], 4) if preds else current,
                    'change_pct':  change or 0.0,
                    'trend':       '📈 UP' if (change or 0) > 0 else '📉 DOWN',
                    'predictions': [round(p, 4) for p in (preds or [current]*24)],
                    'metrics':     metrics or {}
                }
                m = metrics or {}
                print(f"  ✅ {col}: {current:.4f} → {results['exchange_rates'][col]['next_1h']:.4f} "
                      f"({change:+.3f}%) | MAE={m.get('MAE','N/A')} RMSE={m.get('RMSE','N/A')} "
                      f"MAPE={m.get('MAPE','N/A')}% R²={m.get('R2','N/A')}")

    # ── Crypto predictions ──
    crypto_file = os.path.join(DATA_DIR, 'crypto_prices.csv')
    if os.path.exists(crypto_file):
        df = pd.read_csv(crypto_file)
        for col in ['BTC_USD', 'ETH_USD', 'BNB_USD']:
            if col in df.columns and df[col].notna().sum() >= 10:
                preds, change, metrics = predict_next_24h(df[col], col)
                current = float(df[col].dropna().iloc[-1])
                results['crypto'][col] = {
                    'current':     round(current, 2),
                    'next_1h':     round(preds[0], 2) if preds else current,
                    'next_24h':    round(preds[-1], 2) if preds else current,
                    'change_pct':  change or 0.0,
                    'trend':       '📈 UP' if (change or 0) > 0 else '📉 DOWN',
                    'predictions': [round(p, 2) for p in (preds or [current]*24)],
                    'metrics':     metrics or {}
                }
                m = metrics or {}
                print(f"  ✅ {col}: ${current:,.2f} → ${results['crypto'][col]['next_1h']:,.2f} "
                      f"({change:+.3f}%) | MAE={m.get('MAE','N/A')} RMSE={m.get('RMSE','N/A')} "
                      f"MAPE={m.get('MAPE','N/A')}% R²={m.get('R2','N/A')}")

    with open(PRED_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Predictions saved to {PRED_FILE}")
    return results

if __name__ == '__main__':
    run_predictions()

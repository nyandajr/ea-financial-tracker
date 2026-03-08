"""
app.py - East Africa Financial Tracker
Streamlit dashboard for exchange rates, crypto prices & ML predictions
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json, os
from datetime import datetime

st.set_page_config(
    page_title="EA Financial Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR  = os.path.join(os.path.dirname(__file__), '..', 'data')
FX_FILE     = os.path.join(DATA_DIR, 'exchange_rates.csv')
CRYPTO_FILE = os.path.join(DATA_DIR, 'crypto_prices.csv')
PRED_FILE   = os.path.join(DATA_DIR, 'predictions.json')

# ── CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
body, .stApp { background-color: #0D1117; color: #E6EDF3; }
.metric-card {
    background: #161B22; border: 1px solid #30363D;
    border-radius: 10px; padding: 16px; text-align: center;
    margin-bottom: 10px;
}
.metric-value { font-size: 1.8em; font-weight: bold; color: #58A6FF; }
.metric-label { font-size: 0.85em; color: #8B949E; margin-bottom: 4px; }
.trend-up   { color: #3FB950; font-size: 1.1em; }
.trend-down { color: #F85149; font-size: 1.1em; }
.last-update { color: #8B949E; font-size: 0.78em; }
h1,h2,h3 { color: #E6EDF3 !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────
def load_predictions():
    if os.path.exists(PRED_FILE):
        with open(PRED_FILE) as f:
            return json.load(f)
    return {}

def metric_card(label, value, change_pct, unit=''):
    trend_class = 'trend-up' if change_pct >= 0 else 'trend-down'
    arrow = '▲' if change_pct >= 0 else '▼'
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{unit}{value:,.2f}</div>
        <div class="{trend_class}">{arrow} {abs(change_pct):.2f}% (next 1h)</div>
    </div>
    """, unsafe_allow_html=True)

def plot_history(df, col, title, color='#58A6FF'):
    if col not in df.columns or df[col].isna().all():
        st.info(f"No data yet for {col}")
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df[col],
        mode='lines', name=col,
        line=dict(color=color, width=2),
        fill='tozeroy', fillcolor=color.replace(')', ',0.1)').replace('rgb', 'rgba')
    ))
    fig.update_layout(
        title=title, height=280,
        paper_bgcolor='#161B22', plot_bgcolor='#0D1117',
        font=dict(color='#E6EDF3'),
        xaxis=dict(gridcolor='#21262D'),
        yaxis=dict(gridcolor='#21262D'),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_predictions(preds_list, current, label, color='#3FB950'):
    fig = go.Figure()
    hours = list(range(1, 25))
    fig.add_hline(y=current, line_dash='dash', line_color='#8B949E',
                  annotation_text='Current')
    fig.add_trace(go.Scatter(
        x=hours, y=preds_list, mode='lines+markers',
        name='Prediction', line=dict(color=color, width=2),
        marker=dict(size=4)
    ))
    fig.update_layout(
        title=f'{label} — Next 24h Prediction',
        height=260,
        paper_bgcolor='#161B22', plot_bgcolor='#0D1117',
        font=dict(color='#E6EDF3'),
        xaxis=dict(title='Hours from now', gridcolor='#21262D'),
        yaxis=dict(gridcolor='#21262D'),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 EA Financial Tracker")
    st.markdown("---")
    page = st.radio("Navigate", ["🏠 Dashboard", "💱 Exchange Rates", "🪙 Crypto", "🤖 ML Predictions"])
    st.markdown("---")
    if st.button("🔄 Refresh Data Now"):
        import subprocess, sys
        script = os.path.join(os.path.dirname(__file__), 'fetch_data.py')
        subprocess.run([sys.executable, script])
        pred_script = os.path.join(os.path.dirname(__file__), 'predict.py')
        subprocess.run([sys.executable, pred_script])
        st.success("✅ Data refreshed!")
        st.rerun()
    st.markdown("---")
    st.markdown("**Auto-updates:** Every hour ⏱️")
    st.markdown("**Data sources:**")
    st.markdown("- [Frankfurter API](https://www.frankfurter.app)")
    st.markdown("- [CoinGecko API](https://coingecko.com)")

# ── Load data ─────────────────────────────────────────────────
preds = load_predictions()
fx_df = pd.read_csv(FX_FILE) if os.path.exists(FX_FILE) else pd.DataFrame()
cr_df = pd.read_csv(CRYPTO_FILE) if os.path.exists(CRYPTO_FILE) else pd.DataFrame()
last_update = preds.get('generated_at', 'Never')

# ═══════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    st.markdown("# 📊 East Africa Financial Tracker")
    st.markdown(f"<div class='last-update'>Last updated: {last_update} UTC | Auto-refreshes every hour</div>",
                unsafe_allow_html=True)
    st.markdown("---")

    # Exchange Rate Cards
    st.markdown("### 💱 Exchange Rates (vs USD)")
    fx_preds = preds.get('exchange_rates', {})
    cols = st.columns(4)
    pairs = [('USD_TZS','TZS','#58A6FF'), ('USD_KES','KES','#3FB950'),
             ('USD_UGX','UGX','#D29922'), ('USD_EUR','EUR','#A371F7')]
    for i, (col_name, label, color) in enumerate(pairs):
        with cols[i]:
            if col_name in fx_preds:
                d = fx_preds[col_name]
                metric_card(f"USD → {label}", d['current'], d['change_pct'])
            elif not fx_df.empty and col_name in fx_df.columns:
                val = fx_df[col_name].dropna().iloc[-1]
                metric_card(f"USD → {label}", val, 0.0)
            else:
                st.markdown(f"<div class='metric-card'><div class='metric-label'>USD → {label}</div><div class='metric-value'>—</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Crypto Cards
    st.markdown("### 🪙 Crypto Prices (USD)")
    cr_preds = preds.get('crypto', {})
    cols2 = st.columns(3)
    cryptos = [('BTC_USD','Bitcoin ₿','#F7931A'), ('ETH_USD','Ethereum Ξ','#627EEA'), ('BNB_USD','BNB','#F3BA2F')]
    for i, (col_name, label, color) in enumerate(cryptos):
        with cols2[i]:
            if col_name in cr_preds:
                d = cr_preds[col_name]
                metric_card(label, d['current'], d['change_pct'], '$')
            elif not cr_df.empty and col_name in cr_df.columns:
                val = cr_df[col_name].dropna().iloc[-1]
                metric_card(label, val, 0.0, '$')
            else:
                st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>—</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Quick charts
    if not fx_df.empty:
        st.markdown("### 📈 Recent Trends")
        c1, c2 = st.columns(2)
        with c1:
            plot_history(fx_df, 'USD_TZS', 'USD → TZS', '#58A6FF')
        with c2:
            plot_history(fx_df, 'USD_KES', 'USD → KES', '#3FB950')

# ═══════════════════════════════════════════════════════════════
# PAGE: EXCHANGE RATES
# ═══════════════════════════════════════════════════════════════
elif page == "💱 Exchange Rates":
    st.markdown("# 💱 Exchange Rates")
    if fx_df.empty:
        st.warning("No data yet. Click **Refresh Data Now** in the sidebar.")
    else:
        tab1, tab2, tab3 = st.tabs(["📊 Charts", "📋 Raw Data", "🤖 Predictions"])
        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                plot_history(fx_df, 'USD_TZS', 'USD → TZS (Tanzanian Shilling)', '#58A6FF')
                plot_history(fx_df, 'USD_UGX', 'USD → UGX (Ugandan Shilling)', '#D29922')
            with c2:
                plot_history(fx_df, 'USD_KES', 'USD → KES (Kenyan Shilling)', '#3FB950')
                plot_history(fx_df, 'USD_EUR', 'USD → EUR (Euro)', '#A371F7')
        with tab2:
            st.dataframe(fx_df.tail(48).sort_values('timestamp', ascending=False), use_container_width=True)
        with tab3:
            fx_preds = preds.get('exchange_rates', {})
            if not fx_preds:
                st.info("Run a refresh to generate predictions.")
            else:
                for col, d in fx_preds.items():
                    st.markdown(f"**{col}** — Current: `{d['current']}` → Next 1h: `{d['next_1h']}` {d['trend']}")
                    plot_predictions(d['predictions'], d['current'], col)

# ═══════════════════════════════════════════════════════════════
# PAGE: CRYPTO
# ═══════════════════════════════════════════════════════════════
elif page == "🪙 Crypto":
    st.markdown("# 🪙 Crypto Prices")
    if cr_df.empty:
        st.warning("No data yet. Click **Refresh Data Now** in the sidebar.")
    else:
        tab1, tab2, tab3 = st.tabs(["📊 Charts", "📋 Raw Data", "🤖 Predictions"])
        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                plot_history(cr_df, 'BTC_USD', 'Bitcoin (USD)', '#F7931A')
                plot_history(cr_df, 'BNB_USD', 'BNB (USD)', '#F3BA2F')
            with c2:
                plot_history(cr_df, 'ETH_USD', 'Ethereum (USD)', '#627EEA')
        with tab2:
            st.dataframe(cr_df.tail(48).sort_values('timestamp', ascending=False), use_container_width=True)
        with tab3:
            cr_preds = preds.get('crypto', {})
            if not cr_preds:
                st.info("Run a refresh to generate predictions.")
            else:
                for col, d in cr_preds.items():
                    st.markdown(f"**{col}** — Current: `${d['current']:,.2f}` → Next 1h: `${d['next_1h']:,.2f}` {d['trend']}")
                    plot_predictions(d['predictions'], d['current'], col, '#F7931A')

# ═══════════════════════════════════════════════════════════════
# PAGE: ML PREDICTIONS
# ═══════════════════════════════════════════════════════════════
elif page == "🤖 ML Predictions":
    st.markdown("# 🤖 ML Predictions")
    st.info("Model: **Linear Regression** on lag features | Predicts next **24 hours**")

    if not preds:
        st.warning("No predictions yet. Click **Refresh Data Now** in the sidebar.")
    else:
        st.markdown(f"*Generated at: {last_update} UTC*")
        st.markdown("---")

        st.markdown("### 💱 Exchange Rate Predictions")
        for col, d in preds.get('exchange_rates', {}).items():
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(col, f"{d['current']:,.4f}")
            c2.metric("Next 1h", f"{d['next_1h']:,.4f}", f"{d['change_pct']:+.3f}%")
            c3.metric("Next 24h", f"{d['next_24h']:,.4f}")
            c4.metric("Trend", d['trend'])
            plot_predictions(d['predictions'], d['current'], col)
            st.markdown("---")

        st.markdown("### 🪙 Crypto Predictions")
        for col, d in preds.get('crypto', {}).items():
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(col, f"${d['current']:,.2f}")
            c2.metric("Next 1h", f"${d['next_1h']:,.2f}", f"{d['change_pct']:+.3f}%")
            c3.metric("Next 24h", f"${d['next_24h']:,.2f}")
            c4.metric("Trend", d['trend'])
            plot_predictions(d['predictions'], d['current'], col, '#F7931A')
            st.markdown("---")

st.markdown("---")
st.markdown("<center><small>📊 EA Financial Tracker | Built with Streamlit, scikit-learn & free APIs</small></center>",
            unsafe_allow_html=True)

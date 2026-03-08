#!/bin/bash
# ============================================================
#  EA Financial Tracker - Hourly Auto Update + Git Commit
#  Runs every hour via cron, fetches data, predicts, commits
#  Sends email summary to freddynyanda@proton.me
# ============================================================

PROJECT_DIR="/home/fred/Downloads/Python_Projects/EA_Financial_Tracker"
VENV="$PROJECT_DIR/.venv/bin/activate"
LOG="$PROJECT_DIR/logs/auto_update.log"
EMAIL="freddynyanda@proton.me"
SENDER="freddynyanda@gmail.com"

mkdir -p "$PROJECT_DIR/logs"

echo "========================================" >> "$LOG"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting update..." >> "$LOG"

# Activate venv
source "$VENV"

# 1. Fetch new data
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Fetching data..." >> "$LOG"
python3 "$PROJECT_DIR/src/fetch_data.py" >> "$LOG" 2>&1

# 2. Run ML predictions
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running predictions..." >> "$LOG"
python3 "$PROJECT_DIR/src/predict.py" >> "$LOG" 2>&1

# 3. Git add + commit + push
cd "$PROJECT_DIR"
git add data/exchange_rates.csv data/crypto_prices.csv data/predictions.json 2>/dev/null

# Only commit if there are changes
if ! git diff --cached --quiet; then
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
    git commit -m "data: Hourly update - $TIMESTAMP" >> "$LOG" 2>&1
    git push origin main >> "$LOG" 2>&1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Committed and pushed!" >> "$LOG"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  No changes to commit" >> "$LOG"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Done." >> "$LOG"

# ── Email Summary ────────────────────────────────────────────
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Extract latest predictions from JSON
PREDICTIONS=$(python3 - << 'PYEOF'
import json, os
f = os.path.expanduser("/home/fred/Downloads/Python_Projects/EA_Financial_Tracker/data/predictions.json")
try:
    d = json.load(open(f))
    lines = []
    lines.append("=== EXCHANGE RATES ===")
    for k, v in d.get("exchange_rates", {}).items():
        m = v.get("metrics", {})
        lines.append(f"  {k}: {v['current']} -> {v['next_1h']} ({v['change_pct']:+.3f}%) {v['trend']}  | MAPE={m.get('MAPE','N/A')}%  R2={m.get('R2','N/A')}")
    lines.append("")
    lines.append("=== CRYPTO ===")
    for k, v in d.get("crypto", {}).items():
        m = v.get("metrics", {})
        lines.append(f"  {k}: ${v['current']:,.2f} -> ${v['next_1h']:,.2f} ({v['change_pct']:+.3f}%) {v['trend']}  | MAPE={m.get('MAPE','N/A')}%  R2={m.get('R2','N/A')}")
    lines.append("")
    lines.append(f"Generated at: {d.get('generated_at','N/A')} UTC")
    print("\n".join(lines))
except Exception as e:
    print(f"Could not load predictions: {e}")
PYEOF
)

# Send email
{
echo "To: $EMAIL"
echo "From: $SENDER"
echo "Subject: 📊 EA Financial Tracker — Hourly Update $TIMESTAMP"
echo "Content-Type: text/plain; charset=UTF-8"
echo ""
echo "Hello Freddy,"
echo ""
echo "Your EA Financial Tracker has completed its hourly update."
echo ""
echo "$PREDICTIONS"
echo ""
echo "---"
echo "✅ Data committed & pushed to GitHub"
echo "🔗 https://github.com/nyandajr/ea-financial-tracker"
echo ""
echo "Next update in ~1 hour."
echo "— EA Financial Tracker Bot"
} | msmtp "$EMAIL" >> "$LOG" 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Email sent to $EMAIL" >> "$LOG"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  Email failed (check msmtp config)" >> "$LOG"
fi

#!/bin/bash
# ============================================================
#  EA Financial Tracker - Hourly Auto Update + Git Commit
#  Runs every hour via cron, fetches data, predicts, commits
# ============================================================

PROJECT_DIR="/home/fred/Downloads/Python_Projects/EA_Financial_Tracker"
VENV="$PROJECT_DIR/.venv/bin/activate"
LOG="$PROJECT_DIR/logs/auto_update.log"

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

#!/bin/bash
# Lightweight position monitor - Night Trader Edition
# Runs during market hours to check for alerts

PROJECT_ROOT="$(dirname "$(readlink -f "$0")")/.."
LOG_FILE="$PROJECT_ROOT/logs/monitor.log"

# Ensure log dir exists
mkdir -p "$PROJECT_ROOT/logs"

# Get position check result
cd "$PROJECT_ROOT"
RESULT=$(./src/paper-trader.py check 2>&1)

# Log the check
echo "$(date '+%Y-%m-%d %H:%M:%S') | $RESULT" >> "$LOG_FILE"

# Check if there are actual alerts
if echo "$RESULT" | grep -qE "HIT STOP|HIT TARGET|moved [+-]?[5-9]|moved [+-]?[0-9]{2}"; then
    echo "⚠️ ALERT: $RESULT"
    exit 1
fi

# Silent - no action needed
echo "✅ All positions OK"
exit 0

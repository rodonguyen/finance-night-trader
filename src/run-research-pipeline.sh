#!/usr/bin/env bash
# Run the full R1/R2/Supervisor research pipeline via Claude Code
# Usage: ./src/run-research-pipeline.sh <us|asx>

set -euo pipefail

MARKET="${1:-}"
if [[ -z "$MARKET" || ! "$MARKET" =~ ^(us|asx)$ ]]; then
    echo "Usage: $0 <us|asx>"
    exit 1
fi

PROJECT_DIR="/home/rodo/Documents/finance-night-trader"
LOG_DIR="$PROJECT_DIR/logs"
DATE=$(date '+%Y-%m-%d')
TIME=$(date '+%H:%M')
LOG_FILE="$LOG_DIR/research-${MARKET}-${DATE}.log"

cd "$PROJECT_DIR"

echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') — ${MARKET^^} RESEARCH PIPELINE START ===" | tee -a "$LOG_FILE"

# Build the prompt based on market
if [[ "$MARKET" == "asx" ]]; then
    PROMPT="Run the full R1/R2/Supervisor research pipeline for the ASX session today ($(date '+%A %Y-%m-%d')). The ASX market opens at 10 AM AEST.

Follow the night-trader agent workflow exactly:
1. Step 0: Read prior research (last 2 days memory/asx/, all research/theses/asx/, last scan)
2. Run the ASX market scanner: ./src/market-research.py --market asx
3. Check account status: ./src/paper-trader.py --market asx status
4. Spawn R1 (research-advisor) and R2 (research-advisor-02) in parallel with full prior context
5. Have them debate and produce a joint submission
6. Run Supervisor review on the joint submission
7. If any trades are APPROVED and entry conditions are met at current prices, execute them via ./src/paper-trader.py --market asx buy
8. Write the daily journal to memory/asx/${DATE}.md
9. Log all research to research/scans/asx/ and research/theses/asx/

Be disciplined. No FOMO. Only trade if R:R passes and supervisor approves."
elif [[ "$MARKET" == "us" ]]; then
    PROMPT="Run the full R1/R2/Supervisor research pipeline for the US session today. We operate in AEST (UTC+10). The US market opens at 12:30 AM AEST.

Follow the night-trader agent workflow exactly:
1. Step 0: Read prior research (last 2 days memory/us/, all research/theses/us/, last scan)
2. Run the US market scanner: ./src/market-research.py --market us
3. Check account status: ./src/paper-trader.py --market us status
4. Spawn R1 (research-advisor) and R2 (research-advisor-02) in parallel with full prior context
5. Have them debate and produce a joint submission
6. Run Supervisor review on the joint submission
7. If any trades are APPROVED and entry conditions are met at current prices, execute them via ./src/paper-trader.py --market us buy
8. Write the daily journal to memory/us/$(date '+%Y-%m-%d').md
9. Log all research to research/scans/us/ and research/theses/us/

Check existing positions (UEC etc.) and manage stops/targets. Be disciplined. No FOMO."
fi

# Run Claude Code in non-interactive mode with the night-trader agent
claude -p "$PROMPT" \
    --agent night-trader \
    --dangerously-skip-permissions \
    --model opus \
    --max-budget-usd 5.00 \
    --verbose \
    2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') — ${MARKET^^} RESEARCH PIPELINE END (exit: $EXIT_CODE) ===" | tee -a "$LOG_FILE"

exit $EXIT_CODE

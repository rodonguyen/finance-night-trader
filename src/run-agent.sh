#!/usr/bin/env bash
# Run Claude agent for Night Trader market events
# Usage: ./src/run-agent.sh <market> <event>
#
# Events:
#   pre-market     — Full R1/R2/Supervisor research pipeline (Opus, night-trader, $5)
#   market-open    — Review research, execute approved setups (Opus, night-trader, $2)
#   position-check — Quick position & market check (Haiku, position-advisor, $0.25)
#   mid-session    — Full review, trail stops, new setups (Haiku, night-trader, $0.50)
#   market-close   — Close day trades, journal, P&L (Haiku, night-trader, $1)

set -euo pipefail

MARKET="${1:-}"
EVENT="${2:-}"

if [[ -z "$MARKET" || ! "$MARKET" =~ ^(us|asx)$ ]]; then
    echo "Usage: $0 <us|asx> <pre-market|market-open|position-check|mid-session|market-close>"
    exit 1
fi

if [[ -z "$EVENT" ]]; then
    echo "Usage: $0 <us|asx> <pre-market|market-open|position-check|mid-session|market-close>"
    exit 1
fi

PROJECT_DIR="/home/rodo/Documents/finance-night-trader"
DATE=$(date '+%Y-%m-%d')
DAY=$(date '+%A')
TIME=$(date '+%H:%M')
LOG_FILE="$PROJECT_DIR/logs/agent-${MARKET}-${DATE}.log"

cd "$PROJECT_DIR"

# Market-specific context
if [[ "$MARKET" == "asx" ]]; then
    MKT_UPPER="ASX"
    MKT_CLOSE="4 PM AEST"
    MKT_OPEN="10 AM AEST"
    CURRENCY="A$"
else
    MKT_UPPER="US"
    MKT_CLOSE="7 AM AEST"
    MKT_OPEN="12:30 AM AEST"
    CURRENCY="$"
fi

# Configure agent, model, budget, and prompt per event
case "$EVENT" in

  pre-market)
    AGENT="night-trader"
    MODEL="opus"
    BUDGET="5.00"
    PROMPT="Run the full R1/R2/Supervisor research pipeline for the ${MKT_UPPER} session today (${DAY} ${DATE}). Market opens at ${MKT_OPEN}.

Follow the night-trader agent workflow exactly:
1. Step 0: Read prior research (last 2 days memory/${MARKET}/, all research/theses/${MARKET}/, last scan)
2. Run the market scanner: ./src/market-research.py --market ${MARKET}
3. Check account status: ./src/paper-trader.py --market ${MARKET} status
4. Spawn R1 (research-advisor) and R2 (research-advisor-02) in parallel with full prior context
5. Have them debate and produce a joint submission
6. Run Supervisor review on the joint submission
7. If any trades are APPROVED and entry conditions are met, execute via ./src/paper-trader.py --market ${MARKET} buy
8. Write the daily journal to memory/${MARKET}/${DATE}.md
9. Log all research to research/scans/${MARKET}/ and research/theses/${MARKET}/

Be disciplined. No FOMO. Only trade if R:R passes and supervisor approves."
    ;;

  market-open)
    AGENT="night-trader"
    MODEL="opus"
    BUDGET="2.00"
    PROMPT="${MKT_UPPER} market is now OPEN. Today is ${DAY} ${DATE}, ${TIME} AEST.

You are Night Trader. The market just opened — this is a KEY DECISION POINT. Radical changes can happen at the open.

Steps:
1. Read today's approved research: research/scans/${MARKET}/${DATE}-joint.md and research/scans/${MARKET}/${DATE}-supervisor.md
2. If today's research doesn't exist yet, read the MOST RECENT joint submission and supervisor review from research/scans/${MARKET}/
3. Read today's journal: memory/${MARKET}/${DATE}.md (if exists)
4. Run fresh market scan: ./src/market-research.py --market ${MARKET}
5. Check account status: ./src/paper-trader.py --market ${MARKET} status
6. Compare current prices to ALL approved entry zones from today's research
7. For each approved setup: Is the entry condition met? Is R:R still valid at current price? Is the thesis still intact?
8. If YES to all three: EXECUTE the trade via ./src/paper-trader.py --market ${MARKET} buy SYMBOL --dollars AMOUNT --stop STOP --target TARGET --thesis \"THESIS\" --type TYPE
9. If NO: Log why the setup is not confirming and what price level would trigger it
10. Check existing positions — any stops hit overnight? Any gaps?
11. Update the daily journal with open decisions

Report ALL decisions with reasoning. This is the most important check of the day."
    ;;

  position-check)
    AGENT="position-advisor"
    MODEL="haiku"
    BUDGET="0.25"
    PROMPT="Quick ${MKT_UPPER} position & market check. ${DAY} ${DATE}, ${TIME} AEST.

Steps:
1. Run: ./src/paper-trader.py --market ${MARKET} check
2. Run: ./src/paper-trader.py --market ${MARKET} status

IF POSITIONS EXIST:
3. For each position: get current price via ./src/market-research.py --market ${MARKET} or check the output above
4. Compare against stop and target levels
5. Apply the exit framework:
   - Day trades: At 1:1 R:R move stop to breakeven. At 2:1 take 75%. At close exit all.
   - Swing trades: At 1:1 move stop to breakeven. At 2:1 take 50%, trail rest.
   - Position trades: At 1:1 move stop to breakeven. At 2:1 take 25%, widen trail.
6. If any position needs action (stop hit, target reached, trail needed, thesis broken):
   - Execute via ./src/paper-trader.py --market ${MARKET} sell SYMBOL (for exits)
   - Or update stop via ./src/paper-trader.py --market ${MARKET} stop SYMBOL NEW_STOP (for trails)
7. Log any position changes to research/theses/${MARKET}/SYMBOL.md

IF NO POSITIONS:
3. Note any watchlist names that have moved significantly (>3%)
4. Read today's watchlist from memory/${MARKET}/${DATE}.md (if exists)
5. If any watchlist name has reached its approved entry zone, flag it (but do NOT execute — market-open or mid-session handles new entries)

Be concise. This runs every 10 minutes."
    ;;

  mid-session)
    AGENT="night-trader"
    MODEL="haiku"
    BUDGET="0.50"
    PROMPT="${MKT_UPPER} mid-session review. ${DAY} ${DATE}, ${TIME} AEST. Market closes at ${MKT_CLOSE}.

You are Night Trader. This is the mid-session review — more thorough than 10-min checks.

Steps:
1. Full portfolio status: ./src/paper-trader.py --market ${MARKET} status
2. Run market scan: ./src/market-research.py --market ${MARKET}
3. Read today's research: research/scans/${MARKET}/${DATE}-joint.md (or most recent)
4. Read today's journal: memory/${MARKET}/${DATE}.md

FOR OPEN POSITIONS:
5. Full position review — should we trail stops? Take partials? Exit?
6. Has the thesis changed since the morning research?
7. Apply exit framework per trade type

FOR WATCHLIST:
8. Have any approved setups reached entry conditions since market open?
9. If yes and R:R still works: EXECUTE via ./src/paper-trader.py --market ${MARKET} buy
10. Are there any NEW developments (news, earnings, sector moves) that create opportunities not in the morning research? If significant, note for tomorrow's pipeline.

11. Update the daily journal: memory/${MARKET}/${DATE}.md with mid-session notes
12. Log all decisions with reasoning"
    ;;

  market-close)
    AGENT="night-trader"
    MODEL="haiku"
    BUDGET="1.00"
    PROMPT="${MKT_UPPER} market is CLOSING. ${DAY} ${DATE}, ${TIME} AEST.

You are Night Trader. End of session duties:

Steps:
1. Final portfolio status: ./src/paper-trader.py --market ${MARKET} status
2. Run final market scan: ./src/market-research.py --market ${MARKET}

DAY TRADE EXITS:
3. Check ALL positions — any DAY TRADES must be closed NOW (before ${MKT_CLOSE})
4. If day trades exist: ./src/paper-trader.py --market ${MARKET} sell SYMBOL for each
5. Day trades CANNOT be held overnight. No exceptions.

SWING/POSITION REVIEW:
6. Review swing and position trades — are stops appropriate for overnight hold?
7. Any news or events overnight that could gap the position?
8. If holding through: confirm thesis is still valid

DAILY SUMMARY:
9. Run: ./src/paper-trader.py --market ${MARKET} history
10. Calculate daily P&L (realized + unrealized)
11. Update daily journal: memory/${MARKET}/${DATE}.md with:
    - Final P&L
    - Trades executed today (entries + exits)
    - Lessons learned
    - Tomorrow's watchlist and plan
12. Log all final decisions

This is the end of the trading day. Be thorough in the journal."
    ;;

  *)
    echo "Unknown event: $EVENT"
    echo "Valid events: pre-market, market-open, position-check, mid-session, market-close"
    exit 1
    ;;
esac

echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') — ${MKT_UPPER} ${EVENT^^} START (${MODEL}, ${AGENT}) ===" | tee -a "$LOG_FILE"

# Run Claude Code
claude -p "$PROMPT" \
    --agent "$AGENT" \
    --dangerously-skip-permissions \
    --model "$MODEL" \
    --max-budget-usd "$BUDGET" \
    2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') — ${MKT_UPPER} ${EVENT^^} END (exit: $EXIT_CODE) ===" | tee -a "$LOG_FILE"

exit $EXIT_CODE

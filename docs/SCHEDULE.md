# Trading Schedule

## Combined Schedule (AEST)

Every cron event invokes a Claude agent via `./src/run-agent.sh <market> <event>`.

| Time | Market | Event | Agent | Model | Budget |
|------|--------|-------|-------|-------|--------|
| 8:15 AM | ASX | Pre-market research (R1/R2/Supervisor) | night-trader | Opus | $5.00 |
| 10:00 AM | ASX | Market open — review & execute | night-trader | Opus | $2.00 |
| 10:10-3:50 | ASX | Position checks (every 10 min) | position-advisor | Haiku | $0.25 |
| 1:00 PM | ASX | Mid-session review | night-trader | Haiku | $0.50 |
| 4:00 PM | ASX | Market close — day trade exits, journal | night-trader | Haiku | $1.00 |
| 4:10 PM | ASX | Auto-commit research | — | git | — |
| 7:15 PM | US | Pre-market research (R1/R2/Supervisor) | night-trader | Opus | $5.00 |
| 12:30 AM | US | Market open — review & execute | night-trader | Opus | $2.00 |
| 12:40-6:50 | US | Position checks (every 10 min) | position-advisor | Haiku | $0.25 |
| 3:00 AM | US | Mid-session review | night-trader | Haiku | $0.50 |
| 7:00 AM | US | Market close — day trade exits, journal | night-trader | Haiku | $1.00 |
| 7:10 AM | US | Auto-commit + push research | — | git | — |

### Estimated Daily Cost
- ASX: ~$5 (research) + $2 (open) + ~$5.40 (36 checks) + $0.50 (mid) + $1 (close) = **~$14/day**
- US: ~$5 (research) + $2 (open) + ~$5.85 (39 checks) + $0.50 (mid) + $1 (close) = **~$14/day**
- **Combined: ~$28/day** when both markets active

---

## ASX Daily Routine

### 8:15 AM — Pre-Market Research (Opus, night-trader, $5)
```bash
./src/run-agent.sh asx pre-market
```
Full R1/R2/Supervisor pipeline:
1. Reads prior research (Step 0)
2. Runs market scanner for fresh data
3. Spawns R1 + R2 in parallel with full context
4. R1/R2 debate and produce joint submission
5. Supervisor reviews and approves/rejects
6. Executes approved trades if entry conditions met
7. Writes daily journal and research logs

### 10:00 AM — Market Open (Opus, night-trader, $2)
```bash
./src/run-agent.sh asx market-open
```
Critical decision point. Claude reviews approved research, gets fresh prices, and executes any setups that are confirming. Uses Opus because radical changes can happen at the open.

### 10:10 AM - 3:50 PM — Position Checks (Haiku, position-advisor, $0.25)
```bash
./src/run-agent.sh asx position-check
```
Runs every 10 minutes. When positions exist: checks stops, targets, applies exit framework. When flat: monitors watchlist for significant moves. Lightweight — Haiku model keeps cost low.

### 1:00 PM — Mid-Session Review (Haiku, night-trader, $0.50)
```bash
./src/run-agent.sh asx mid-session
```
More thorough than 10-min checks. Trail stops, take partials, scan for new setups not in morning research, update journal.

### 4:00 PM — Market Close (Haiku, night-trader, $1)
```bash
./src/run-agent.sh asx market-close
```
Close all day trades (mandatory). Review swing/position holds. Calculate P&L. Write daily journal with trades, lessons, tomorrow's plan.

---

## US Daily Routine

### 7:15 PM — Pre-Market Research (Opus, night-trader, $5)
```bash
./src/run-agent.sh us pre-market
```
Same R1/R2/Supervisor pipeline as ASX. Also reviews existing positions (UEC etc.).

### 12:30 AM — Market Open (Opus, night-trader, $2)
```bash
./src/run-agent.sh us market-open
```
Same as ASX open — review research, execute confirmed setups.

### 12:40 AM - 6:50 AM — Position Checks (Haiku, position-advisor, $0.25)
```bash
./src/run-agent.sh us position-check
```
Same as ASX — every 10 minutes.

### 3:00 AM — Mid-Session Review (Haiku, night-trader, $0.50)
```bash
./src/run-agent.sh us mid-session
```

### 7:00 AM — Market Close (Haiku, night-trader, $1)
```bash
./src/run-agent.sh us market-close
```

---

## Quick Commands

```bash
# Manually trigger any event
./src/run-agent.sh asx pre-market
./src/run-agent.sh asx market-open
./src/run-agent.sh asx position-check
./src/run-agent.sh asx mid-session
./src/run-agent.sh asx market-close
./src/run-agent.sh us pre-market
./src/run-agent.sh us market-open

# Check agent logs
tail -100 logs/agent-asx-$(date '+%Y-%m-%d').log
tail -100 logs/agent-us-$(date '+%Y-%m-%d').log

# Raw Python scripts (still available for manual use)
./src/paper-trader.py --market asx status
./src/paper-trader.py --market asx check
./src/market-research.py --market asx
./src/paper-trader.py --market us status
./src/paper-trader.py --market us buy AAPL --dollars 2000 --stop 180 --target 200 --thesis "reason"
./src/paper-trader.py --market asx sell BHP
```

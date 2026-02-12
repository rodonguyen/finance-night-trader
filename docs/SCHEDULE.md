# Trading Schedule

## Combined Schedule (AEST)

| Time | Market | Action | Type |
|------|--------|--------|------|
| 8:00 AM | ASX | Pre-market scan | Cron (script) |
| **8:15 AM** | **ASX** | **Full R1/R2/Supervisor research pipeline** | **Cron (Claude agent)** |
| 10:00 AM | ASX | Market open, execute setups | Cron (script) |
| 10:10 AM - 3:50 PM | ASX | Position checks (every 10 min) | Cron (script) |
| 1:00 PM | ASX | Mid-session review | Cron (script) |
| 4:00 PM | ASX | Market close, daily summary | Cron (script) |
| 4:10 PM | ASX | Auto-commit research | Cron (git) |
| 7:00 PM | US | Pre-market scan | Cron (script) |
| **7:15 PM** | **US** | **Full R1/R2/Supervisor research pipeline** | **Cron (Claude agent)** |
| 12:30 AM | US | Market open, execute setups | Cron (script) |
| 12:40 AM - 6:50 AM | US | Position checks (every 10 min) | Cron (script) |
| 3:00 AM | US | Mid-session review | Cron (script) |
| 7:00 AM | US | Market close, daily summary | Cron (script) |
| 7:10 AM | US | Auto-commit + push research | Cron (git) |

---

## ASX Daily Routine

### 8:00 AM — Pre-Market Scan (automated)
```bash
./src/market-research.py --market asx
```
Runs via cron. Produces raw market data (indices, sectors, movers).

### 8:15 AM — Research Pipeline (automated via Claude agent)
```bash
./src/run-research-pipeline.sh asx
```
Runs via cron. Claude agent (night-trader) orchestrates:
1. Reads prior research (Step 0)
2. Spawns R1 + R2 in parallel
3. R1/R2 debate and produce joint submission
4. Supervisor reviews and approves/rejects
5. Executes any approved trades if conditions are met
6. Writes daily journal and research logs

**Budget cap: $5 USD per session.** Logs to `logs/research-asx-YYYY-MM-DD.log`.

### 10:00 AM — Market Open
```bash
./src/paper-trader.py --market asx status
./src/market-research.py --market asx
```

**Tasks:**
1. Check if pre-market setups are confirming
2. Verify thesis still valid
3. Execute confirmed setups
4. Document decisions

### 10:10 AM - 3:50 PM — Trading Session

**Every 10 mins:**
```bash
./src/paper-trader.py --market asx check
```

**If alerts:**
- Review position
- Apply exit framework
- Execute if needed

### 1:00 PM — Mid-Session Review
```bash
./src/paper-trader.py --market asx status
```

**Tasks:**
1. Full position review
2. Trail stops if appropriate
3. Take partials at targets
4. Scan for new setups

### 4:00 PM — Market Close
```bash
./src/paper-trader.py --market asx status
./src/paper-trader.py --market asx history
```

**Tasks:**
1. Close all day trades
2. Calculate daily P&L
3. Log lessons learned
4. Update memory file

---

## US Daily Routine

### 7:00 PM — Pre-Market Scan (automated)
```bash
./src/market-research.py --market us
```
Runs via cron. Produces raw market data.

### 7:15 PM — Research Pipeline (automated via Claude agent)
```bash
./src/run-research-pipeline.sh us
```
Runs via cron. Same Claude agent pipeline as ASX (R1/R2/Supervisor).
Also checks existing positions (stops, targets, management).

**Budget cap: $5 USD per session.** Logs to `logs/research-us-YYYY-MM-DD.log`.

### 12:30 AM — Market Open
```bash
./src/paper-trader.py --market us status
./src/market-research.py --market us
```

**Tasks:**
1. Check if pre-market setups are confirming
2. Verify thesis still valid
3. Execute confirmed setups
4. Document decisions

### 12:40 AM - 6:50 AM — Trading Session

**Every 10 mins:**
```bash
./src/paper-trader.py --market us check
```

**If alerts:**
- Review position
- Apply exit framework
- Execute if needed

### 3:00 AM — Mid-Session Review
```bash
./src/paper-trader.py --market us status
```

**Tasks:**
1. Full position review
2. Trail stops if appropriate
3. Take partials at targets
4. Scan for new setups

### 7:00 AM — Market Close
```bash
./src/paper-trader.py --market us status
./src/paper-trader.py --market us history
```

**Tasks:**
1. Close all day trades
2. Calculate daily P&L
3. Log lessons learned
4. Update memory file

---

## Quick Commands

```bash
# US status
./src/paper-trader.py --market us status

# ASX status
./src/paper-trader.py --market asx status

# US alerts
./src/paper-trader.py --market us check

# ASX alerts
./src/paper-trader.py --market asx check

# US trade
./src/paper-trader.py --market us buy AAPL --dollars 2000 --stop 180 --target 200 --thesis "reason"

# ASX trade
./src/paper-trader.py --market asx buy BHP --dollars 2000 --stop 40 --target 50 --thesis "reason"

# Exit trade
./src/paper-trader.py --market us sell AAPL
./src/paper-trader.py --market asx sell BHP

# Manually trigger research pipeline
./src/run-research-pipeline.sh asx
./src/run-research-pipeline.sh us

# Check research pipeline logs
tail -100 logs/research-asx-$(date '+%Y-%m-%d').log
tail -100 logs/research-us-$(date '+%Y-%m-%d').log
```

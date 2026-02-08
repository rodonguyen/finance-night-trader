# Trading Schedule

## Daily Routine (AEST)

### 7:00 PM — Pre-Market Scan
```bash
cd /home/rodo/Documents/finance-night-trader.py
./src/market-research.py
```

**Tasks:**
1. Run market scanner
2. Research each mover (web search)
3. Build watchlist with entry/stop/target
4. Document in `memory/YYYY-MM-DD.md`
5. NO TRADES — just research

### 12:30 AM — Market Open
```bash
./src/paper-trader.py status
./src/market-research.py
```

**Tasks:**
1. Check if pre-market setups are confirming
2. Verify thesis still valid
3. Execute confirmed setups
4. Document decisions

### 12:40 AM - 6:50 AM — Trading Session

**Every 10 mins:**
```bash
./src/paper-trader.py check
```

**If alerts:**
- Review position
- Apply exit framework
- Execute if needed

### 3:00 AM — Mid-Session Review
```bash
./src/paper-trader.py status
```

**Tasks:**
1. Full position review
2. Trail stops if appropriate
3. Take partials at targets
4. Scan for new setups

### 7:00 AM — Market Close
```bash
./src/paper-trader.py status
./src/paper-trader.py history
```

**Tasks:**
1. Close all day trades
2. Calculate daily P&L
3. Log lessons learned
4. Update memory file

---

## Cron Equivalent (Manual Triggers)

Since Claude Code doesn't have automatic crons, run these manually:

| Time | Command | Purpose |
|------|---------|---------|
| 7:00 PM | `./src/market-research.py` | Pre-market scan |
| 12:30 AM | `./src/paper-trader.py status` | Market open |
| 3:00 AM | `./src/paper-trader.py status` | Mid-session |
| 7:00 AM | `./src/paper-trader.py history` | Daily close |

## Quick Commands

```bash
# Full status
./src/paper-trader.py status

# Quick alerts only
./src/paper-trader.py check

# Execute trade
./src/paper-trader.py buy SYMBOL --dollars 400 --stop X --target Y --thesis "reason"

# Exit trade
./src/paper-trader.py sell SYMBOL
```

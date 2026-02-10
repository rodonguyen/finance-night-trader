# Trading Schedule

## Combined Schedule (AEST)

| Time | Market | Action |
|------|--------|--------|
| 8:00 AM | ASX | Pre-market scan |
| 10:00 AM | ASX | Market open, execute setups |
| 10:10 AM - 3:50 PM | ASX | Position checks (every 10 min) |
| 1:00 PM | ASX | Mid-session review |
| 4:00 PM | ASX | Market close, daily summary |
| 7:00 PM | US | Pre-market scan |
| 12:30 AM | US | Market open, execute setups |
| 12:40 AM - 6:50 AM | US | Position checks (every 10 min) |
| 3:00 AM | US | Mid-session review |
| 7:00 AM | US | Market close, daily summary |

---

## ASX Daily Routine

### 8:00 AM — Pre-Market Scan
```bash
./src/market-research.py --market asx
```

**Tasks:**
1. Run ASX market scanner
2. Research movers (web search for news)
3. Build watchlist with entry/stop/target
4. Document in `memory/asx/YYYY-MM-DD.md`
5. NO TRADES — just research

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

### 7:00 PM — Pre-Market Scan
```bash
./src/market-research.py --market us
```

**Tasks:**
1. Run US market scanner
2. Research movers (web search for news)
3. Build watchlist with entry/stop/target
4. Document in `memory/us/YYYY-MM-DD.md`
5. NO TRADES — just research

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
```

# Night Trader

Autonomous paper trading system for US and ASX markets.

## Quick Reference

```bash
# Check US account
./src/paper-trader.py --market us status

# Check ASX account
./src/paper-trader.py --market asx status

# Run US market scan
./src/market-research.py --market us

# Run ASX market scan
./src/market-research.py --market asx

# Execute US trade
./src/paper-trader.py --market us buy SYMBOL --dollars 2000 --stop X --target Y --thesis "reason"

# Execute ASX trade
./src/paper-trader.py --market asx buy SYMBOL --dollars 2000 --stop X --target Y --thesis "reason"

# Close position
./src/paper-trader.py --market us sell SYMBOL
./src/paper-trader.py --market asx sell SYMBOL

# Check alerts
./src/paper-trader.py --market us check
./src/paper-trader.py --market asx check
```

Note: `--market us` is the default if omitted.

## Project Structure

```
.
├── CLAUDE.md           # This file
├── README.md           # Project overview
├── src/                # Executable scripts
│   ├── paper-trader.py    # Trading CLI (--market us|asx)
│   ├── market-research.py # Market scanner (--market us|asx)
│   └── position-monitor
├── config/
│   └── trading-config.json  # Multi-market config
├── data/
│   ├── positions-us.json    # US paper positions (gitignored)
│   └── positions-asx.json   # ASX paper positions (gitignored)
├── memory/             # Trading journal (by market)
│   ├── us/YYYY-MM-DD.md
│   └── asx/YYYY-MM-DD.md
├── research/           # All research output (by market)
│   ├── scans/
│   │   ├── us/YYYY-MM-DD.md
│   │   └── asx/YYYY-MM-DD.md
│   ├── theses/
│   │   ├── us/SYMBOL.md
│   │   └── asx/SYMBOL.md
│   └── themes/
│       ├── us/theme-name.md
│       └── asx/theme-name.md
├── logs/               # Execution logs (gitignored)
│   ├── trades-us.log
│   └── trades-asx.log
└── docs/
    └── SCHEDULE.md     # Trading schedule (both markets)
```

## Risk Rules

| Rule | US (USD) | ASX (AUD) |
|------|----------|-----------|
| Capital | $10,000 | A$10,000 |
| Max position | $2,000 (20%) | A$2,000 (20%) |
| Max risk/trade | $200 (2%) | A$200 (2%) |
| Min R:R | 2:1 | 2:1 |
| Max daily loss | $500 | A$500 |
| Max positions | 5 | 5 |

**Never break these rules.**

## Trade Types

| Type | Timeframe | When to Use |
|------|-----------|-------------|
| Day Trade | In/out same session | Momentum plays, earnings reactions, gap fills |
| Swing Trade | Hold 2-10 days | Technical setups, catalyst anticipation |
| Position Trade | Hold weeks/months | Thematic plays (bottleneck owners) |

## Trading Schedule (AEST)

| Time | Market | Action |
|------|--------|--------|
| 8:00 AM | ASX | Pre-market scan |
| 10:00 AM | ASX | Market open, execute setups |
| 1:00 PM | ASX | Mid-session review |
| 4:00 PM | ASX | Market close, daily summary |
| 7:00 PM | US | Pre-market scan |
| 12:30 AM | US | Market open, execute setups |
| 3:00 AM | US | Mid-session review |
| 7:00 AM | US | Market close, daily summary |

## Workflow

### Pre-Market
1. Run `./src/market-research.py --market <us|asx>`
2. Research movers (web search for news)
3. Build watchlist with entry/stop/target
4. Log in `memory/<us|asx>/YYYY-MM-DD.md`

### Market Open
1. Check if setups are confirming
2. Verify thesis still valid
3. Execute if confirmed: `./src/paper-trader.py --market <us|asx> buy ...`
4. Log all decisions

### Position Management

**Day Trades:**
```
At 1:1 R:R → Move stop to breakeven
At 2:1 R:R → Take 75%, trail rest tight
At market close → Exit remaining (no overnight)
```

**Swing Trades:**
```
At 1:1 R:R → Move stop to breakeven
At 2:1 R:R → Take 50%, trail rest
At 3:1+ R:R → Trail tight (5%)
After 10 days → Re-evaluate or close
```

**Position Trades:**
```
At 1:1 R:R → Move stop to breakeven
At 2:1 R:R → Take 25%, widen trail
At 3:1+ R:R → Take another 25%, trail rest
Weekly thesis review → Continue/reduce/exit
```

### Market Close
1. Close all day trades
2. Review swing/position trades
3. Calculate daily P&L
4. Log lessons in memory file

## Entry Checklist

Before any trade:
- [ ] Clear thesis with catalyst
- [ ] Trade type classified (day/swing/position)
- [ ] R:R ≥ 2:1
- [ ] Position ≤ $2,000 / A$2,000
- [ ] Stop makes sense (support/structure)
- [ ] Not at max positions (5)
- [ ] Not at daily loss limit

## Research Logging Protocol

All research output MUST be logged to `research/<market>/`. This is the institutional record.

### `research/scans/<us|asx>/YYYY-MM-DD.md` — Daily Market Scans
Log every market scan session: indices, sectors, movers, opportunities found, and what was passed on and why.

### `research/theses/<us|asx>/SYMBOL.md` — Stock Theses (one file per symbol, append updates)
Log every thesis review: bull/bear case, verdict, entry/stop/target levels, edge identification, and sources. Append new reviews as dated entries so the file becomes a running history of analysis on that symbol.

### `research/themes/<us|asx>/theme-name.md` — Thematic Research (one file per theme)
Log deep-dive research on investment themes: signal scoring, value chain mapping, bottleneck analysis, lifecycle positioning, and watchlist names. Update as the theme evolves.

### `memory/<us|asx>/YYYY-MM-DD.md` — Trading Journal (decisions + lessons only)
Brief daily log: trades executed, decisions made, P&L, lessons learned, tomorrow's watchlist. Keep this concise — the detail lives in `research/`.

**Before session:** Read last 2 days of `memory/<market>/YYYY-MM-DD.md` and any relevant `research/theses/<market>/` files for open positions.

**After session:** Update memory and research files.

## Code Style

When modifying scripts:
- Python 3, no external deps except requests
- Use pathlib for paths
- Relative paths from project root
- Log all trades to `logs/trades-<market>.log`
- Always pass `--market` flag to scripts

## Context

This system runs parallel to Rodai (OpenClaw) for performance comparison:
- Starting capital: $10,000 USD + A$10,000 AUD
- Same percentage-based risk rules (20% max position, 2% max risk)
- Different decision-making
- Separate position tracking per market

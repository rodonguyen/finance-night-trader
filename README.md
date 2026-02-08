# Finance Night Trader 🌙

Paper trading system for US markets, designed for Claude Code.

## Setup

```bash
cd /home/rodo/Documents/finance-night-trader.py

# Test it works
./src/paper-trader.py status
```

## Usage

```bash
# Market scan
./src/market-research.py

# Buy
./src/paper-trader.py buy AAPL --dollars 400 --stop 180 --target 200 --thesis "reason"

# Sell
./src/paper-trader.py sell AAPL

# Check alerts
./src/paper-trader.py check

# Trade history
./src/paper-trader.py history
```

## Risk Rules

- **Capital:** $2,000
- **Max position:** $400 (20%)
- **Max risk/trade:** $40 (2%)
- **Min R:R:** 2:1
- **Max daily loss:** $100

## Schedule (AEST)

| Time | Action |
|------|--------|
| 7 PM | Pre-market scan |
| 12:30 AM | Market open |
| 3 AM | Mid-session |
| 7 AM | Market close |

## Structure

```
├── CLAUDE.md        # Claude Code instructions
├── src/             # Scripts
├── config/          # Configuration
├── data/            # Positions (gitignored)
├── memory/          # Trading journal
├── logs/            # Logs (gitignored)
└── docs/            # Documentation
```

## Comparison

This runs parallel to Rodai (OpenClaw) with separate position tracking for performance comparison.

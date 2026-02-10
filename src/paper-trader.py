#!/usr/bin/env python3
"""
Local Paper Trading System - Night Trader Edition
Supports US and ASX markets via --market flag
Uses Finnhub for prices, tracks positions in JSON
"""

import json
import os
import sys
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Get project root (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / 'config' / 'trading-config.json'

# Ensure directories exist
(PROJECT_ROOT / 'data').mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / 'logs').mkdir(parents=True, exist_ok=True)

# Load config
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

FINNHUB_KEY = CONFIG.get('finnhub_api_key')
BRISBANE = timezone(timedelta(hours=10))

# Market context — set by parse_args()
MARKET = 'us'
MARKET_CONFIG = None
RISK_RULES = None
POSITIONS_PATH = None
TRADES_LOG = None
CURRENCY_SYMBOL = '$'

def init_market(market):
    """Initialize market-specific config"""
    global MARKET, MARKET_CONFIG, RISK_RULES, POSITIONS_PATH, TRADES_LOG, CURRENCY_SYMBOL
    MARKET = market
    MARKET_CONFIG = CONFIG['markets'][market]
    RISK_RULES = MARKET_CONFIG['risk_rules']
    POSITIONS_PATH = PROJECT_ROOT / MARKET_CONFIG['positions_file']
    TRADES_LOG = PROJECT_ROOT / MARKET_CONFIG['trades_log']
    CURRENCY_SYMBOL = MARKET_CONFIG.get('currency_symbol', '$')
    POSITIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRADES_LOG.parent.mkdir(parents=True, exist_ok=True)

def load_positions():
    if POSITIONS_PATH.exists():
        with open(POSITIONS_PATH) as f:
            return json.load(f)
    else:
        capital = MARKET_CONFIG['capital']
        return {
            "account": {
                "starting_capital": capital,
                "cash": capital,
                "created_at": datetime.now(BRISBANE).strftime("%Y-%m-%d")
            },
            "positions": [],
            "closed_trades": [],
            "daily_pnl": {}
        }

def save_positions(data):
    with open(POSITIONS_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def log_trade(action, symbol, qty, price, pnl=None, thesis=None):
    """Log trade to file"""
    timestamp = datetime.now(BRISBANE).strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{timestamp} | {MARKET.upper()} | {action} | {symbol} | qty={qty:.6f} | price={CURRENCY_SYMBOL}{price:.2f}"
    if pnl is not None:
        log_line += f" | P&L={CURRENCY_SYMBOL}{pnl:+.2f}"
    if thesis:
        log_line += f" | thesis={thesis[:50]}"

    with open(TRADES_LOG, 'a') as f:
        f.write(log_line + "\n")

def get_price(symbol):
    """Get current price from Finnhub"""
    finnhub_symbol = symbol

    # Handle crypto symbols (US market only)
    if MARKET == 'us' and symbol.endswith('USD') and len(symbol) > 4:
        crypto = symbol[:-3]
        finnhub_symbol = f"BINANCE:{crypto}USDT"
    elif MARKET == 'asx':
        suffix = MARKET_CONFIG.get('finnhub_suffix', '.AX')
        # Don't double-add suffix
        if not symbol.endswith(suffix):
            finnhub_symbol = f"{symbol}{suffix}"

    url = f"https://finnhub.io/api/v1/quote?symbol={finnhub_symbol}&token={FINNHUB_KEY}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('c') and data['c'] > 0:
            return float(data['c'])
    except:
        pass

    # Fallback: try without suffix modification
    if finnhub_symbol != symbol:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            if data.get('c') and data['c'] > 0:
                return float(data['c'])
        except:
            pass

    return None

def status():
    """Show account status and positions"""
    data = load_positions()
    account = data['account']
    positions = data['positions']

    market_label = MARKET.upper()
    total_value = account['cash']

    print(f"🌙 **NIGHT TRADER - {market_label} PAPER ACCOUNT ({MARKET_CONFIG['currency']})**")
    print(f"💵 Cash: {CURRENCY_SYMBOL}{account['cash']:,.2f}")

    if positions:
        print(f"\n📈 **OPEN POSITIONS**")
        for pos in positions:
            price = get_price(pos['symbol'])
            if price:
                entry = pos['entry_price']
                qty = pos['qty']
                market_value = price * qty
                pnl = (price - entry) * qty
                pnl_pct = ((price / entry) - 1) * 100
                total_value += market_value

                emoji = "🟢" if pnl >= 0 else "🔴"
                print(f"{emoji} {pos['symbol']}: {qty:.4f} @ {CURRENCY_SYMBOL}{entry:.2f} → {CURRENCY_SYMBOL}{price:.2f} ({pnl_pct:+.2f}%) P&L: {CURRENCY_SYMBOL}{pnl:+.2f}")
                print(f"   Stop: {CURRENCY_SYMBOL}{pos.get('stop', 'N/A')} | Target: {CURRENCY_SYMBOL}{pos.get('target', 'N/A')}")
                if pos.get('thesis'):
                    print(f"   Thesis: {pos['thesis'][:60]}...")
            else:
                print(f"⚠️ {pos['symbol']}: Unable to fetch price")
                total_value += pos['entry_price'] * pos['qty']
    else:
        print(f"\n📈 **POSITIONS**\nNo open positions")

    print(f"\n💰 **TOTAL EQUITY: {CURRENCY_SYMBOL}{total_value:,.2f}**")
    starting = account['starting_capital']
    total_pnl = total_value - starting
    total_pnl_pct = ((total_value / starting) - 1) * 100
    print(f"📈 Total P&L: {CURRENCY_SYMBOL}{total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)")

    print(f"\n⚠️ **RISK STATUS**")
    print(f"   Max position: {CURRENCY_SYMBOL}{RISK_RULES['max_position_size']}")
    print(f"   Positions: {len(positions)}/{RISK_RULES['max_concurrent_positions']}")

def buy(symbol, dollars=None, qty=None, stop=None, target=None, thesis=None):
    """Open a long position"""
    data = load_positions()

    if len(data['positions']) >= RISK_RULES['max_concurrent_positions']:
        print(f"❌ Max concurrent positions ({RISK_RULES['max_concurrent_positions']}) reached")
        return

    for pos in data['positions']:
        if pos['symbol'] == symbol:
            print(f"❌ Already have position in {symbol}")
            return

    price = get_price(symbol)
    if not price:
        print(f"❌ Could not get price for {symbol}")
        return

    if dollars:
        qty = dollars / price
    elif not qty:
        print("❌ Must specify --dollars or --qty")
        return

    cost = price * qty

    if cost > data['account']['cash']:
        print(f"❌ Insufficient cash. Need {CURRENCY_SYMBOL}{cost:.2f}, have {CURRENCY_SYMBOL}{data['account']['cash']:.2f}")
        return

    max_pos = RISK_RULES['max_position_size']
    if cost > max_pos:
        print(f"⚠️ Position {CURRENCY_SYMBOL}{cost:.2f} exceeds max {CURRENCY_SYMBOL}{max_pos}. Reducing to {CURRENCY_SYMBOL}{max_pos}.")
        qty = max_pos / price
        cost = max_pos

    if stop and target:
        risk_per_share = price - stop
        reward_per_share = target - price
        if risk_per_share > 0:
            rr = reward_per_share / risk_per_share
            if rr < RISK_RULES['min_rr_ratio']:
                print(f"⚠️ R:R ratio {rr:.1f}:1 below minimum {RISK_RULES['min_rr_ratio']}:1")
                print("   Proceeding anyway - consider adjusting levels")

    position = {
        'symbol': symbol,
        'side': 'long',
        'qty': qty,
        'entry_price': price,
        'entry_time': datetime.now(BRISBANE).isoformat(),
        'stop': stop,
        'target': target,
        'thesis': thesis,
        'trade_type': None
    }

    data['positions'].append(position)
    data['account']['cash'] -= cost
    save_positions(data)
    log_trade('BUY', symbol, qty, price, thesis=thesis)

    print(f"✅ BOUGHT {qty:.6f} {symbol} @ {CURRENCY_SYMBOL}{price:.2f}")
    print(f"   Cost: {CURRENCY_SYMBOL}{cost:.2f}")
    if stop:
        risk = (price - stop) * qty
        print(f"   Stop: {CURRENCY_SYMBOL}{stop} (Risk: {CURRENCY_SYMBOL}{risk:.2f})")
    if target:
        reward = (target - price) * qty
        print(f"   Target: {CURRENCY_SYMBOL}{target} (Reward: {CURRENCY_SYMBOL}{reward:.2f})")
        if stop:
            rr = (target - price) / (price - stop)
            print(f"   R:R: {rr:.1f}:1")

def sell(symbol, qty=None, dollars=None):
    """Close a position (full or partial)"""
    data = load_positions()

    pos_idx = None
    for i, pos in enumerate(data['positions']):
        if pos['symbol'] == symbol:
            pos_idx = i
            break

    if pos_idx is None:
        print(f"❌ No position in {symbol}")
        return

    pos = data['positions'][pos_idx]
    price = get_price(symbol)
    if not price:
        print(f"❌ Could not get price for {symbol}")
        return

    if qty is None and dollars is None:
        qty = pos['qty']
    elif dollars:
        qty = min(dollars / price, pos['qty'])
    else:
        qty = min(qty, pos['qty'])

    proceeds = price * qty
    entry = pos['entry_price']
    pnl = (price - entry) * qty
    pnl_pct = ((price / entry) - 1) * 100

    if qty >= pos['qty']:
        closed_trade = {
            **pos,
            'exit_price': price,
            'exit_time': datetime.now(BRISBANE).isoformat(),
            'pnl': pnl,
            'pnl_pct': pnl_pct
        }
        data['closed_trades'].append(closed_trade)
        data['positions'].pop(pos_idx)
    else:
        data['positions'][pos_idx]['qty'] -= qty

    data['account']['cash'] += proceeds
    save_positions(data)
    log_trade('SELL', symbol, qty, price, pnl=pnl)

    emoji = "🟢" if pnl >= 0 else "🔴"
    print(f"{emoji} SOLD {qty:.6f} {symbol} @ {CURRENCY_SYMBOL}{price:.2f}")
    print(f"   P&L: {CURRENCY_SYMBOL}{pnl:+.2f} ({pnl_pct:+.2f}%)")
    print(f"   Cash: {CURRENCY_SYMBOL}{data['account']['cash']:,.2f}")

def update_stop(symbol, new_stop):
    """Update stop loss for a position"""
    data = load_positions()

    for pos in data['positions']:
        if pos['symbol'] == symbol:
            old_stop = pos.get('stop', 'N/A')
            pos['stop'] = new_stop
            save_positions(data)
            print(f"✅ {symbol} stop updated: {CURRENCY_SYMBOL}{old_stop} → {CURRENCY_SYMBOL}{new_stop}")
            return

    print(f"❌ No position in {symbol}")

def check_alerts():
    """Check if any positions hit stop or target"""
    data = load_positions()
    alerts = []

    for pos in data['positions']:
        price = get_price(pos['symbol'])
        if not price:
            continue

        symbol = pos['symbol']
        entry = pos['entry_price']
        pnl_pct = ((price / entry) - 1) * 100

        if pos.get('stop') and price <= pos['stop']:
            alerts.append(f"🚨 {symbol} HIT STOP @ {CURRENCY_SYMBOL}{price:.2f} (Stop: {CURRENCY_SYMBOL}{pos['stop']})")

        if pos.get('target') and price >= pos['target']:
            alerts.append(f"🎯 {symbol} HIT TARGET @ {CURRENCY_SYMBOL}{price:.2f} (Target: {CURRENCY_SYMBOL}{pos['target']})")

        if abs(pnl_pct) > 5:
            emoji = "📈" if pnl_pct > 0 else "📉"
            alerts.append(f"{emoji} {symbol} moved {pnl_pct:+.1f}% ({CURRENCY_SYMBOL}{price:.2f})")

    if alerts:
        print(f"🌙 **NIGHT TRADER ALERTS ({MARKET.upper()})**")
        for alert in alerts:
            print(alert)
        return True
    else:
        print(f"✅ All {MARKET.upper()} positions within normal range")
        return False

def history():
    """Show closed trades"""
    data = load_positions()

    if not data['closed_trades']:
        print(f"No closed {MARKET.upper()} trades yet")
        return

    print(f"📜 **TRADE HISTORY ({MARKET.upper()})**")
    total_pnl = 0
    wins = 0
    losses = 0

    for trade in data['closed_trades'][-10:]:
        emoji = "🟢" if trade['pnl'] >= 0 else "🔴"
        print(f"{emoji} {trade['symbol']}: {CURRENCY_SYMBOL}{trade['pnl']:+.2f} ({trade['pnl_pct']:+.1f}%)")
        if trade.get('thesis'):
            print(f"   Thesis: {trade['thesis'][:50]}")
        total_pnl += trade['pnl']
        if trade['pnl'] >= 0:
            wins += 1
        else:
            losses += 1

    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    print(f"\n📊 Total: {CURRENCY_SYMBOL}{total_pnl:+.2f} | Win rate: {wins}/{wins+losses} ({win_rate:.0f}%)")

def reset():
    """Reset paper account"""
    capital = MARKET_CONFIG['capital']
    data = {
        "account": {
            "starting_capital": capital,
            "cash": capital,
            "created_at": datetime.now(BRISBANE).strftime("%Y-%m-%d")
        },
        "positions": [],
        "closed_trades": [],
        "daily_pnl": {}
    }
    save_positions(data)
    print(f"✅ {MARKET.upper()} account reset to {CURRENCY_SYMBOL}{capital:,}")

if __name__ == "__main__":
    # Parse --market flag before subcommand
    args = sys.argv[1:]
    market = 'us'  # default

    if '--market' in args:
        idx = args.index('--market')
        if idx + 1 < len(args):
            market = args[idx + 1].lower()
            args = args[:idx] + args[idx+2:]
        else:
            print("❌ --market requires a value: us or asx")
            sys.exit(1)

    if market not in CONFIG.get('markets', {}):
        print(f"❌ Unknown market: {market}. Available: {', '.join(CONFIG['markets'].keys())}")
        sys.exit(1)

    init_market(market)

    if len(args) < 1:
        print(f"🌙 Night Trader - Paper Trading System ({market.upper()})")
        print("\nUsage: paper-trader.py [--market us|asx] <command> [args]")
        print("Commands: status, buy, sell, stop, check, history, reset")
        print("\nExamples:")
        print("  paper-trader.py status")
        print("  paper-trader.py --market asx status")
        print("  paper-trader.py buy AAPL --dollars 2000 --stop 180 --target 200 --thesis 'Earnings momentum'")
        print("  paper-trader.py --market asx buy BHP --dollars 2000 --stop 40 --target 50 --thesis 'Iron ore rally'")
        print("  paper-trader.py sell AAPL")
        sys.exit(1)

    cmd = args[0].lower()

    if cmd == 'status':
        status()
    elif cmd == 'buy':
        if len(args) < 2:
            print("Usage: paper-trader.py [--market us|asx] buy SYMBOL [--dollars X | --qty X] [--stop X] [--target X] [--thesis 'reason']")
            sys.exit(1)
        symbol = args[1].upper()
        dollars = None
        qty = None
        stop = None
        target = None
        thesis = None

        i = 2
        while i < len(args):
            if args[i] == '--dollars':
                dollars = float(args[i+1])
                i += 2
            elif args[i] == '--qty':
                qty = float(args[i+1])
                i += 2
            elif args[i] == '--stop':
                stop = float(args[i+1])
                i += 2
            elif args[i] == '--target':
                target = float(args[i+1])
                i += 2
            elif args[i] == '--thesis':
                thesis = args[i+1]
                i += 2
            elif args[i] == '--type':
                # trade_type handled at position level
                i += 2
            else:
                i += 1

        buy(symbol, dollars=dollars, qty=qty, stop=stop, target=target, thesis=thesis)
    elif cmd == 'sell':
        if len(args) < 2:
            print("Usage: paper-trader.py [--market us|asx] sell SYMBOL [--qty X | --dollars X]")
            sys.exit(1)
        symbol = args[1].upper()
        qty = None
        dollars = None

        i = 2
        while i < len(args):
            if args[i] == '--qty':
                qty = float(args[i+1])
                i += 2
            elif args[i] == '--dollars':
                dollars = float(args[i+1])
                i += 2
            else:
                i += 1

        sell(symbol, qty=qty, dollars=dollars)
    elif cmd == 'stop':
        if len(args) < 3:
            print("Usage: paper-trader.py [--market us|asx] stop SYMBOL PRICE")
            sys.exit(1)
        update_stop(args[1].upper(), float(args[2]))
    elif cmd == 'check':
        check_alerts()
    elif cmd == 'history':
        history()
    elif cmd == 'reset':
        reset()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

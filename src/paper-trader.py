#!/usr/bin/env python3
"""
Local Paper Trading System - Night Trader Edition
Uses Finnhub for prices, tracks positions in JSON
Standalone version for Claude Code
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
POSITIONS_PATH = PROJECT_ROOT / 'data' / 'positions.json'
TRADES_LOG = PROJECT_ROOT / 'logs' / 'trades.log'

# Ensure directories exist
POSITIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
TRADES_LOG.parent.mkdir(parents=True, exist_ok=True)

# Load config
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

FINNHUB_KEY = CONFIG.get('finnhub_api_key')
BRISBANE = timezone(timedelta(hours=10))

# Risk rules
RISK_RULES = CONFIG.get('risk_rules', {
    'max_position_size': 400,
    'max_risk_per_trade': 40,
    'max_daily_loss': 100,
    'min_rr_ratio': 2,
    'max_concurrent_positions': 5
})

def load_positions():
    if POSITIONS_PATH.exists():
        with open(POSITIONS_PATH) as f:
            return json.load(f)
    else:
        # Initialize fresh account
        return {
            "account": {
                "starting_capital": 2000,
                "cash": 2000,
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
    log_line = f"{timestamp} | {action} | {symbol} | qty={qty:.6f} | price=${price:.2f}"
    if pnl is not None:
        log_line += f" | P&L=${pnl:+.2f}"
    if thesis:
        log_line += f" | thesis={thesis[:50]}"
    
    with open(TRADES_LOG, 'a') as f:
        f.write(log_line + "\n")

def get_price(symbol):
    """Get current price from Finnhub"""
    # Handle crypto symbols
    if symbol.endswith('USD') and len(symbol) > 4:
        crypto = symbol[:-3]
        finnhub_symbol = f"BINANCE:{crypto}USDT"
    else:
        finnhub_symbol = symbol
    
    url = f"https://finnhub.io/api/v1/quote?symbol={finnhub_symbol}&token={FINNHUB_KEY}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('c') and data['c'] > 0:
            return float(data['c'])
    except:
        pass
    
    # Fallback for stocks
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
    
    # Calculate total equity
    total_value = account['cash']
    
    print(f"🌙 **NIGHT TRADER - PAPER ACCOUNT**")
    print(f"💵 Cash: ${account['cash']:,.2f}")
    
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
                print(f"{emoji} {pos['symbol']}: {qty:.4f} @ ${entry:.2f} → ${price:.2f} ({pnl_pct:+.2f}%) P&L: ${pnl:+.2f}")
                print(f"   Stop: ${pos.get('stop', 'N/A')} | Target: ${pos.get('target', 'N/A')}")
                if pos.get('thesis'):
                    print(f"   Thesis: {pos['thesis'][:60]}...")
            else:
                print(f"⚠️ {pos['symbol']}: Unable to fetch price")
                total_value += pos['entry_price'] * pos['qty']
    else:
        print(f"\n📈 **POSITIONS**\nNo open positions")
    
    print(f"\n💰 **TOTAL EQUITY: ${total_value:,.2f}**")
    starting = account['starting_capital']
    total_pnl = total_value - starting
    total_pnl_pct = ((total_value / starting) - 1) * 100
    print(f"📈 Total P&L: ${total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)")
    
    # Show risk status
    print(f"\n⚠️ **RISK STATUS**")
    print(f"   Max position: ${RISK_RULES['max_position_size']}")
    print(f"   Positions: {len(positions)}/{RISK_RULES['max_concurrent_positions']}")

def buy(symbol, dollars=None, qty=None, stop=None, target=None, thesis=None):
    """Open a long position"""
    data = load_positions()
    
    # Check max concurrent positions
    if len(data['positions']) >= RISK_RULES['max_concurrent_positions']:
        print(f"❌ Max concurrent positions ({RISK_RULES['max_concurrent_positions']}) reached")
        return
    
    # Check if already in position
    for pos in data['positions']:
        if pos['symbol'] == symbol:
            print(f"❌ Already have position in {symbol}")
            return
    
    price = get_price(symbol)
    if not price:
        print(f"❌ Could not get price for {symbol}")
        return
    
    # Calculate quantity
    if dollars:
        qty = dollars / price
    elif not qty:
        print("❌ Must specify --dollars or --qty")
        return
    
    cost = price * qty
    
    # Check cash
    if cost > data['account']['cash']:
        print(f"❌ Insufficient cash. Need ${cost:.2f}, have ${data['account']['cash']:.2f}")
        return
    
    # Check position size limit
    max_pos = RISK_RULES['max_position_size']
    if cost > max_pos:
        print(f"⚠️ Position ${cost:.2f} exceeds max ${max_pos}. Reducing to ${max_pos}.")
        qty = max_pos / price
        cost = max_pos
    
    # Validate R:R if stop and target provided
    if stop and target:
        risk_per_share = price - stop
        reward_per_share = target - price
        if risk_per_share > 0:
            rr = reward_per_share / risk_per_share
            if rr < RISK_RULES['min_rr_ratio']:
                print(f"⚠️ R:R ratio {rr:.1f}:1 below minimum {RISK_RULES['min_rr_ratio']}:1")
                print("   Proceeding anyway - consider adjusting levels")
    
    # Open position
    position = {
        'symbol': symbol,
        'side': 'long',
        'qty': qty,
        'entry_price': price,
        'entry_time': datetime.now(BRISBANE).isoformat(),
        'stop': stop,
        'target': target,
        'thesis': thesis
    }
    
    data['positions'].append(position)
    data['account']['cash'] -= cost
    save_positions(data)
    log_trade('BUY', symbol, qty, price, thesis=thesis)
    
    print(f"✅ BOUGHT {qty:.6f} {symbol} @ ${price:.2f}")
    print(f"   Cost: ${cost:.2f}")
    if stop:
        risk = (price - stop) * qty
        print(f"   Stop: ${stop} (Risk: ${risk:.2f})")
    if target:
        reward = (target - price) * qty
        print(f"   Target: ${target} (Reward: ${reward:.2f})")
        if stop:
            rr = (target - price) / (price - stop)
            print(f"   R:R: {rr:.1f}:1")

def sell(symbol, qty=None, dollars=None):
    """Close a position (full or partial)"""
    data = load_positions()
    
    # Find position
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
    
    # Determine quantity to sell
    if qty is None and dollars is None:
        qty = pos['qty']  # Sell all
    elif dollars:
        qty = min(dollars / price, pos['qty'])
    else:
        qty = min(qty, pos['qty'])
    
    proceeds = price * qty
    entry = pos['entry_price']
    pnl = (price - entry) * qty
    pnl_pct = ((price / entry) - 1) * 100
    
    # Update or remove position
    if qty >= pos['qty']:
        # Full close
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
        # Partial close
        data['positions'][pos_idx]['qty'] -= qty
    
    data['account']['cash'] += proceeds
    save_positions(data)
    log_trade('SELL', symbol, qty, price, pnl=pnl)
    
    emoji = "🟢" if pnl >= 0 else "🔴"
    print(f"{emoji} SOLD {qty:.6f} {symbol} @ ${price:.2f}")
    print(f"   P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
    print(f"   Cash: ${data['account']['cash']:,.2f}")

def update_stop(symbol, new_stop):
    """Update stop loss for a position"""
    data = load_positions()
    
    for pos in data['positions']:
        if pos['symbol'] == symbol:
            old_stop = pos.get('stop', 'N/A')
            pos['stop'] = new_stop
            save_positions(data)
            print(f"✅ {symbol} stop updated: ${old_stop} → ${new_stop}")
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
        
        # Check stop
        if pos.get('stop') and price <= pos['stop']:
            alerts.append(f"🚨 {symbol} HIT STOP @ ${price:.2f} (Stop: ${pos['stop']})")
        
        # Check target
        if pos.get('target') and price >= pos['target']:
            alerts.append(f"🎯 {symbol} HIT TARGET @ ${price:.2f} (Target: ${pos['target']})")
        
        # Check significant moves (>5%)
        if abs(pnl_pct) > 5:
            emoji = "📈" if pnl_pct > 0 else "📉"
            alerts.append(f"{emoji} {symbol} moved {pnl_pct:+.1f}% (${price:.2f})")
    
    if alerts:
        print("🌙 **NIGHT TRADER ALERTS**")
        for alert in alerts:
            print(alert)
        return True
    else:
        print("✅ All positions within normal range")
        return False

def history():
    """Show closed trades"""
    data = load_positions()
    
    if not data['closed_trades']:
        print("No closed trades yet")
        return
    
    print("📜 **TRADE HISTORY**")
    total_pnl = 0
    wins = 0
    losses = 0
    
    for trade in data['closed_trades'][-10:]:  # Last 10
        emoji = "🟢" if trade['pnl'] >= 0 else "🔴"
        print(f"{emoji} {trade['symbol']}: ${trade['pnl']:+.2f} ({trade['pnl_pct']:+.1f}%)")
        if trade.get('thesis'):
            print(f"   Thesis: {trade['thesis'][:50]}")
        total_pnl += trade['pnl']
        if trade['pnl'] >= 0:
            wins += 1
        else:
            losses += 1
    
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    print(f"\n📊 Total: ${total_pnl:+.2f} | Win rate: {wins}/{wins+losses} ({win_rate:.0f}%)")

def reset():
    """Reset paper account"""
    data = {
        "account": {
            "starting_capital": 2000,
            "cash": 2000,
            "created_at": datetime.now(BRISBANE).strftime("%Y-%m-%d")
        },
        "positions": [],
        "closed_trades": [],
        "daily_pnl": {}
    }
    save_positions(data)
    print("✅ Night Trader account reset to $2,000")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("🌙 Night Trader - Paper Trading System")
        print("\nUsage: paper-trader.py <command> [args]")
        print("Commands: status, buy, sell, stop, check, history, reset")
        print("\nExamples:")
        print("  paper-trader.py status")
        print("  paper-trader.py buy AAPL --dollars 400 --stop 180 --target 200 --thesis 'Earnings momentum'")
        print("  paper-trader.py sell AAPL")
        print("  paper-trader.py stop AAPL 185")
        print("  paper-trader.py check  (for alerts)")
        sys.exit(1)
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'status':
        status()
    elif cmd == 'buy':
        if len(sys.argv) < 3:
            print("Usage: paper-trader.py buy SYMBOL [--dollars X | --qty X] [--stop X] [--target X] [--thesis 'reason']")
            sys.exit(1)
        symbol = sys.argv[2].upper()
        dollars = None
        qty = None
        stop = None
        target = None
        thesis = None
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == '--dollars':
                dollars = float(sys.argv[i+1])
                i += 2
            elif sys.argv[i] == '--qty':
                qty = float(sys.argv[i+1])
                i += 2
            elif sys.argv[i] == '--stop':
                stop = float(sys.argv[i+1])
                i += 2
            elif sys.argv[i] == '--target':
                target = float(sys.argv[i+1])
                i += 2
            elif sys.argv[i] == '--thesis':
                thesis = sys.argv[i+1]
                i += 2
            else:
                i += 1
        
        buy(symbol, dollars=dollars, qty=qty, stop=stop, target=target, thesis=thesis)
    elif cmd == 'sell':
        if len(sys.argv) < 3:
            print("Usage: paper-trader.py sell SYMBOL [--qty X | --dollars X]")
            sys.exit(1)
        symbol = sys.argv[2].upper()
        qty = None
        dollars = None
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == '--qty':
                qty = float(sys.argv[i+1])
                i += 2
            elif sys.argv[i] == '--dollars':
                dollars = float(sys.argv[i+1])
                i += 2
            else:
                i += 1
        
        sell(symbol, qty=qty, dollars=dollars)
    elif cmd == 'stop':
        if len(sys.argv) < 4:
            print("Usage: paper-trader.py stop SYMBOL PRICE")
            sys.exit(1)
        update_stop(sys.argv[2].upper(), float(sys.argv[3]))
    elif cmd == 'check':
        check_alerts()
    elif cmd == 'history':
        history()
    elif cmd == 'reset':
        reset()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

#!/usr/bin/env python3
"""
Market Research & Pre-Market Scanner - Night Trader Edition
Supports US and ASX markets via --market flag
"""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Get project root (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / 'config' / 'trading-config.json'

# Load config
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

FINNHUB_KEY = CONFIG['finnhub_api_key']
BRISBANE = timezone(timedelta(hours=10))

# Market context — set in main
MARKET = 'us'
MARKET_CONFIG = None

def init_market(market):
    global MARKET, MARKET_CONFIG
    MARKET = market
    MARKET_CONFIG = CONFIG['markets'][market]

def finnhub_get(endpoint, params={}):
    """Make a Finnhub API request"""
    params['token'] = FINNHUB_KEY
    query = '&'.join(f"{k}={v}" for k, v in params.items())
    url = f"https://finnhub.io/api/v1/{endpoint}?{query}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def yahoo_quote(symbol):
    """Get quote from Yahoo Finance (for ASX). Returns Finnhub-compatible dict."""
    # Index symbols start with ^ and are used as-is
    if symbol.startswith('^'):
        yahoo_symbol = symbol
    else:
        suffix = MARKET_CONFIG.get('finnhub_suffix', '.AX')
        yahoo_symbol = symbol if symbol.endswith(suffix) else f"{symbol}{suffix}"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?range=1d&interval=1d"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        meta = data['chart']['result'][0]['meta']
        c = meta.get('regularMarketPrice', 0)
        pc = meta.get('chartPreviousClose', 0) or meta.get('previousClose', 0)
        d = (c - pc) if (c and pc) else 0
        dp = ((d / pc) * 100) if pc else 0
        h = meta.get('regularMarketDayHigh', 0) or c
        l = meta.get('regularMarketDayLow', 0) or c
        return {'c': c, 'pc': pc, 'd': d, 'dp': dp, 'h': h, 'l': l}
    except Exception as e:
        return {"error": str(e)}

def get_quote(symbol):
    """Get current quote for a symbol — Finnhub for US, Yahoo for ASX"""
    if MARKET == 'asx':
        return yahoo_quote(symbol)
    return finnhub_get("quote", {"symbol": symbol})

def get_market_news(category="general"):
    """Get market news"""
    return finnhub_get("news", {"category": category})

def get_company_news(symbol, days=1):
    """Get news for a specific company"""
    finnhub_symbol = symbol
    if MARKET == 'asx':
        # Try Finnhub with .AX suffix for news (may not work on free tier)
        suffix = MARKET_CONFIG.get('finnhub_suffix', '.AX')
        if not symbol.endswith(suffix):
            finnhub_symbol = f"{symbol}{suffix}"
    today = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    result = finnhub_get("company-news", {"symbol": finnhub_symbol, "from": from_date, "to": today})
    # If ASX news fails, try without suffix
    if MARKET == 'asx' and (not isinstance(result, list) or not result):
        result = finnhub_get("company-news", {"symbol": symbol, "from": from_date, "to": today})
    return result

def get_market_status():
    """Check if market is open"""
    exchange = MARKET_CONFIG.get('finnhub_exchange', 'US')
    result = finnhub_get("stock/market-status", {"exchange": exchange})
    # Fallback for ASX: time-based check if Finnhub doesn't support it
    if 'error' in result and MARKET == 'asx':
        now = datetime.now(BRISBANE)
        weekday = now.weekday()  # 0=Mon, 6=Sun
        hour = now.hour
        is_open = (0 <= weekday <= 4) and (10 <= hour < 16)
        return {'isOpen': is_open, 'exchange': 'AS', 'source': 'time-based'}
    return result

def format_quote(symbol, data):
    """Format quote data nicely"""
    if 'error' in data:
        return f"{symbol}: Error - {data['error']}"

    c = data.get('c') or 0
    pc = data.get('pc') or 0
    d = data.get('d') or 0
    dp = data.get('dp') or 0
    h = data.get('h') or 0
    l = data.get('l') or 0

    cs = MARKET_CONFIG.get('currency_symbol', '$')

    if c == 0:
        return f"⚪ {symbol}: No data"

    direction = "🟢" if d >= 0 else "🔴"
    return f"{direction} {symbol}: {cs}{c:.2f} ({dp:+.2f}%) | H: {cs}{h:.2f} L: {cs}{l:.2f}"

# ── US Market Scan ───────────────────────────────────────────────

def scan_us_market():
    """US market scan"""
    output = []
    now = datetime.now(BRISBANE)
    output.append(f"📊 **US MARKET SCAN** — {now.strftime('%Y-%m-%d %H:%M AEST')}\n")

    status = get_market_status()
    if 'isOpen' in status:
        market_state = "🟢 OPEN" if status['isOpen'] else "🔴 CLOSED"
        output.append(f"**US Market:** {market_state}")

    output.append("\n**📈 INDICES & FUTURES**")
    for sym in ['SPY', 'QQQ', 'IWM', 'DIA']:
        output.append(format_quote(sym, get_quote(sym)))

    output.append("\n**🏭 SECTORS**")
    sectors = {'XLK': 'Tech', 'XLF': 'Finance', 'XLE': 'Energy', 'XLV': 'Health'}
    for sym, name in sectors.items():
        q = format_quote(sym, get_quote(sym))
        output.append(q.replace(sym, name))

    output.append("\n**🚀 MAG 7**")
    for sym in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']:
        output.append(format_quote(sym, get_quote(sym)))

    output.append("\n**₿ CRYPTO & PROXIES**")
    for sym in ['COIN', 'MSTR', 'MARA', 'RIOT', 'CLSK']:
        output.append(format_quote(sym, get_quote(sym)))

    output.append("\n**📰 TOP NEWS**")
    news = get_market_news("general")
    if isinstance(news, list):
        for item in news[:5]:
            headline = item.get('headline', '')[:80]
            source = item.get('source', '')
            output.append(f"• {headline}... ({source})")

    return "\n".join(output)

def scan_us_options():
    """Scan for notable options setups based on price movement"""
    output = []
    output.append("\n**📊 OPTIONS SCANNER**")

    hot_stocks = ['AAPL', 'TSLA', 'NVDA', 'AMD', 'SPY', 'QQQ', 'MSFT', 'AMZN', 'META', 'GOOGL']
    setups = []

    for sym in hot_stocks:
        quote = get_quote(sym)
        dp = quote.get('dp') or 0
        c = quote.get('c') or 0

        if abs(dp) >= 2 and c > 0:
            if dp > 0:
                setups.append((sym, dp, "CALLS", "Momentum continuation"))
            else:
                setups.append((sym, dp, "PUTS", "Downside continuation"))
        elif abs(dp) >= 3:
            if dp < 0:
                setups.append((sym, dp, "CALLS", "Oversold bounce"))
            else:
                setups.append((sym, dp, "PUTS", "Overbought fade"))

    if setups:
        setups.sort(key=lambda x: abs(x[1]), reverse=True)
        for sym, dp, opt_type, thesis in setups[:5]:
            output.append(f"• {sym} {dp:+.2f}% → {opt_type} ({thesis})")
    else:
        output.append("No high-conviction options setups (±2%)")

    return "\n".join(output)

def scan_us_crypto():
    """Scan crypto markets via proxy stocks"""
    output = []
    output.append("\n**₿ CRYPTO SCANNER**")

    proxies = ['COIN', 'MSTR', 'MARA', 'RIOT']
    big_movers = []

    for sym in proxies:
        quote = get_quote(sym)
        dp = quote.get('dp') or 0
        if abs(dp) >= 5:
            big_movers.append((sym, dp))

    if big_movers:
        output.append("🔥 Big crypto proxy moves:")
        for sym, dp in sorted(big_movers, key=lambda x: abs(x[1]), reverse=True):
            direction = "📈" if dp > 0 else "📉"
            output.append(f"  {direction} {sym}: {dp:+.2f}%")
        output.append("Consider crypto/proxy plays")
    else:
        output.append("No major crypto proxy moves (±5%)")

    return "\n".join(output)

def find_us_opportunities():
    """Find potential US trading opportunities"""
    output = []
    output.append("\n**🎯 POTENTIAL OPPORTUNITIES**\n")

    watchlist = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
                 'AMD', 'CRM', 'NFLX', 'JPM', 'BAC', 'XOM', 'CVX']

    movers = []
    for sym in watchlist:
        quote = get_quote(sym)
        if 'dp' in quote:
            dp = quote['dp']
            if abs(dp) >= 1.5:
                movers.append((sym, quote))

    if movers:
        movers.sort(key=lambda x: abs(x[1]['dp']), reverse=True)
        for sym, q in movers[:5]:
            dp = q['dp']
            direction = "📈 LONG candidate" if dp > 0 else "📉 SHORT candidate"
            output.append(f"**{sym}**: {dp:+.2f}% — {direction}")

            news = get_company_news(sym, days=1)
            if isinstance(news, list) and news:
                top_news = news[0].get('headline', '')[:60]
                output.append(f"  └ News: {top_news}...")
            output.append("")
    else:
        output.append("No significant movers (±1.5%) found in watchlist")

    return "\n".join(output)

# ── ASX Market Scan ──────────────────────────────────────────────

def scan_asx_market():
    """ASX market scan"""
    output = []
    now = datetime.now(BRISBANE)
    output.append(f"📊 **ASX MARKET SCAN** — {now.strftime('%Y-%m-%d %H:%M AEST')}\n")

    status = get_market_status()
    if 'isOpen' in status:
        market_state = "🟢 OPEN" if status['isOpen'] else "🔴 CLOSED"
        output.append(f"**ASX Market:** {market_state}")

    # ASX Indices (Yahoo uses ^AXJO, ^AORD format)
    output.append("\n**📈 ASX INDICES**")
    indices = {'^AXJO': 'ASX 200', '^AORD': 'All Ords'}
    for sym, name in indices.items():
        q = format_quote(name, get_quote(sym))
        output.append(q)

    # ASX Sectors (Yahoo uses ^AX + sector code)
    output.append("\n**🏭 ASX SECTORS**")
    sectors = {
        '^AXMJ': 'Materials', '^AXEJ': 'Energy', '^AXFJ': 'Financials',
        '^AXIJ': 'IT', '^AXHJ': 'Healthcare'
    }
    for sym, name in sectors.items():
        q = format_quote(name, get_quote(sym))
        output.append(q)

    # Blue Chips
    output.append("\n**🏦 ASX BLUE CHIPS**")
    blue_chips = ['BHP', 'CBA', 'CSL', 'WES', 'NAB', 'ANZ', 'WBC', 'FMG',
                  'RIO', 'WDS', 'GMG', 'TCL', 'ALL', 'REA', 'XRO', 'WTC']
    for sym in blue_chips:
        output.append(format_quote(sym, get_quote(sym)))

    # Mining & Resources
    output.append("\n**⛏️ MINING & RESOURCES**")
    miners = ['PLS', 'LTR', 'MIN', 'IGO', 'SFR', '29M', 'DEV', 'BOE', 'PDN', 'BMN']
    for sym in miners:
        output.append(format_quote(sym, get_quote(sym)))

    # News
    output.append("\n**📰 TOP NEWS**")
    news = get_market_news("general")
    if isinstance(news, list):
        for item in news[:5]:
            headline = item.get('headline', '')[:80]
            source = item.get('source', '')
            output.append(f"• {headline}... ({source})")

    return "\n".join(output)

def find_asx_opportunities():
    """Find potential ASX trading opportunities"""
    output = []
    output.append("\n**🎯 ASX POTENTIAL OPPORTUNITIES**\n")

    watchlist = ['BHP', 'CBA', 'CSL', 'WES', 'NAB', 'ANZ', 'WBC', 'FMG',
                 'RIO', 'WDS', 'PLS', 'LTR', 'MIN', 'IGO', 'SFR',
                 'GMG', 'XRO', 'WTC', 'PME', 'APX',
                 'BOE', 'PDN', 'BMN', 'REA', 'ALL']

    movers = []
    for sym in watchlist:
        quote = get_quote(sym)
        if 'dp' in quote:
            dp = quote['dp']
            if abs(dp) >= 1.5:
                movers.append((sym, quote))

    if movers:
        movers.sort(key=lambda x: abs(x[1]['dp']), reverse=True)
        for sym, q in movers[:5]:
            dp = q['dp']
            direction = "📈 LONG candidate" if dp > 0 else "📉 SHORT candidate"
            output.append(f"**{sym}**: {dp:+.2f}% — {direction}")

            news = get_company_news(sym, days=1)
            if isinstance(news, list) and news:
                top_news = news[0].get('headline', '')[:60]
                output.append(f"  └ News: {top_news}...")
            output.append("")
    else:
        output.append("No significant movers (±1.5%) found in ASX watchlist")

    return "\n".join(output)

# ── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]
    market = 'us'

    if '--market' in args:
        idx = args.index('--market')
        if idx + 1 < len(args):
            market = args[idx + 1].lower()
        else:
            print("❌ --market requires a value: us or asx")
            sys.exit(1)

    if market not in CONFIG.get('markets', {}):
        print(f"❌ Unknown market: {market}. Available: {', '.join(CONFIG['markets'].keys())}")
        sys.exit(1)

    init_market(market)

    if market == 'us':
        print(scan_us_market())
        print(scan_us_crypto())
        print(scan_us_options())
        print(find_us_opportunities())
    elif market == 'asx':
        print(scan_asx_market())
        print(find_asx_opportunities())

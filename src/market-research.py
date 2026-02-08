#!/usr/bin/env python3
"""
Market Research & Pre-Market Scanner - Night Trader Edition
Runs before US market open to identify trading opportunities
"""

import json
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

def get_quote(symbol):
    """Get current quote for a symbol"""
    return finnhub_get("quote", {"symbol": symbol})

def get_market_news(category="general"):
    """Get market news"""
    return finnhub_get("news", {"category": category})

def get_company_news(symbol, days=1):
    """Get news for a specific company"""
    today = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return finnhub_get("company-news", {"symbol": symbol, "from": from_date, "to": today})

def get_market_status():
    """Check if US market is open"""
    return finnhub_get("stock/market-status", {"exchange": "US"})

def format_quote(symbol, data):
    """Format quote data nicely"""
    if 'error' in data:
        return f"{symbol}: Error - {data['error']}"
    
    c = data.get('c') or 0  # current
    pc = data.get('pc') or 0  # previous close
    d = data.get('d') or 0  # change
    dp = data.get('dp') or 0  # change percent
    h = data.get('h') or 0  # high
    l = data.get('l') or 0  # low
    
    if c == 0:
        return f"⚪ {symbol}: No data"
    
    direction = "🟢" if d >= 0 else "🔴"
    return f"{direction} {symbol}: ${c:.2f} ({dp:+.2f}%) | H: ${h:.2f} L: ${l:.2f}"

def scan_market():
    """Main market scan"""
    output = []
    now = datetime.now(BRISBANE)
    output.append(f"📊 **MARKET SCAN** — {now.strftime('%Y-%m-%d %H:%M AEST')}\n")
    
    # Market status
    status = get_market_status()
    if 'isOpen' in status:
        market_state = "🟢 OPEN" if status['isOpen'] else "🔴 CLOSED"
        output.append(f"**US Market:** {market_state}")
    
    # Major indices/ETFs
    output.append("\n**📈 INDICES & FUTURES**")
    indices = ['SPY', 'QQQ', 'IWM', 'DIA']
    for sym in indices:
        quote = get_quote(sym)
        output.append(format_quote(sym, quote))
    
    # Key sectors
    output.append("\n**🏭 SECTORS**")
    sectors = ['XLK', 'XLF', 'XLE', 'XLV']  # Tech, Financial, Energy, Healthcare
    sector_names = {'XLK': 'Tech', 'XLF': 'Finance', 'XLE': 'Energy', 'XLV': 'Health'}
    for sym in sectors:
        quote = get_quote(sym)
        name = sector_names.get(sym, sym)
        q = format_quote(sym, quote)
        output.append(f"{q.replace(sym, name)}")
    
    # Mag 7
    output.append("\n**🚀 MAG 7**")
    mag7 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
    for sym in mag7:
        quote = get_quote(sym)
        output.append(format_quote(sym, quote))
    
    # Crypto proxies (Finnhub doesn't have direct crypto quotes easily)
    output.append("\n**₿ CRYPTO & PROXIES**")
    crypto_proxy = ['COIN', 'MSTR', 'MARA', 'RIOT', 'CLSK']
    for sym in crypto_proxy:
        quote = get_quote(sym)
        output.append(format_quote(sym, quote))
    
    # News headlines
    output.append("\n**📰 TOP NEWS**")
    news = get_market_news("general")
    if isinstance(news, list):
        for item in news[:5]:
            headline = item.get('headline', '')[:80]
            source = item.get('source', '')
            output.append(f"• {headline}... ({source})")
    
    return "\n".join(output)

def scan_options_activity():
    """Scan for notable options setups based on price movement"""
    output = []
    output.append("\n**📊 OPTIONS SCANNER**")
    
    # Check volatility and momentum for options plays
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
            # Big move = potential reversal play
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

def scan_crypto():
    """Scan crypto markets via proxy stocks"""
    output = []
    output.append("\n**₿ CRYPTO SCANNER**")
    
    # Crypto proxy stocks - big movers indicate BTC/ETH moves
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

def find_opportunities():
    """Find potential trading opportunities"""
    output = []
    output.append("\n**🎯 POTENTIAL OPPORTUNITIES**\n")
    
    # Check for big movers in major stocks
    watchlist = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 
                 'AMD', 'CRM', 'NFLX', 'JPM', 'BAC', 'XOM', 'CVX']
    
    movers = []
    for sym in watchlist:
        quote = get_quote(sym)
        if 'dp' in quote:
            dp = quote['dp']
            if abs(dp) >= 1.5:  # 1.5%+ move
                movers.append((sym, quote))
    
    if movers:
        movers.sort(key=lambda x: abs(x[1]['dp']), reverse=True)
        for sym, q in movers[:5]:
            dp = q['dp']
            direction = "📈 LONG candidate" if dp > 0 else "📉 SHORT candidate"
            output.append(f"**{sym}**: {dp:+.2f}% — {direction}")
            
            # Get recent news for this stock
            news = get_company_news(sym, days=1)
            if isinstance(news, list) and news:
                top_news = news[0].get('headline', '')[:60]
                output.append(f"  └ News: {top_news}...")
            output.append("")
    else:
        output.append("No significant movers (±1.5%) found in watchlist")
    
    return "\n".join(output)

if __name__ == "__main__":
    print(scan_market())
    print(scan_crypto())
    print(scan_options_activity())
    print(find_opportunities())

"""
FinVerse — Mock Market Data Generator
Produces realistic OHLCV + volume for ~15 stocks.
Deterministic base prices with realistic random walk.
"""
import random
import time
import math
from datetime import datetime, timedelta

# Stock universe with realistic base prices and sector info
STOCKS = {
    "RELIANCE":  {"base": 2850.0, "sector": "Energy",       "vol": 0.018, "name": "Reliance Industries"},
    "TCS":       {"base": 3920.0, "sector": "IT",           "vol": 0.014, "name": "Tata Consultancy Services"},
    "HDFCBANK":  {"base": 1650.0, "sector": "Banking",      "vol": 0.012, "name": "HDFC Bank"},
    "INFY":      {"base": 1480.0, "sector": "IT",           "vol": 0.016, "name": "Infosys"},
    "ICICIBANK": {"base": 1090.0, "sector": "Banking",      "vol": 0.015, "name": "ICICI Bank"},
    "BHARTIARTL":{"base": 1220.0, "sector": "Telecom",      "vol": 0.017, "name": "Bharti Airtel"},
    "SBIN":      {"base": 780.0,  "sector": "Banking",      "vol": 0.020, "name": "State Bank of India"},
    "ITC":       {"base": 465.0,  "sector": "FMCG",         "vol": 0.011, "name": "ITC Limited"},
    "KOTAKBANK": {"base": 1780.0, "sector": "Banking",      "vol": 0.013, "name": "Kotak Mahindra Bank"},
    "LT":        {"base": 3350.0, "sector": "Infrastructure","vol": 0.016, "name": "Larsen & Toubro"},
    "WIPRO":     {"base": 445.0,  "sector": "IT",           "vol": 0.019, "name": "Wipro"},
    "ADANIENT":  {"base": 3100.0, "sector": "Conglomerate", "vol": 0.028, "name": "Adani Enterprises"},
    "TATAMOTORS":{"base": 740.0,  "sector": "Auto",         "vol": 0.022, "name": "Tata Motors"},
    "SUNPHARMA":{"base": 1250.0, "sector": "Pharma",       "vol": 0.014, "name": "Sun Pharma"},
    "MARUTI":    {"base": 11200.0,"sector": "Auto",          "vol": 0.015, "name": "Maruti Suzuki"},
}

# Persistent price state (resets on restart — that's fine for demo)
_price_state: dict[str, float] = {}
_last_tick: dict[str, float] = {}

def _init_price(symbol: str) -> float:
    """Initialize price with slight random offset from base."""
    if symbol not in _price_state:
        base = STOCKS.get(symbol, {}).get("base", 500.0)
        _price_state[symbol] = base * (1 + random.uniform(-0.03, 0.03))
    return _price_state[symbol]


def get_stock_info(symbol: str) -> dict | None:
    """Get static info for a stock."""
    info = STOCKS.get(symbol.upper())
    if not info:
        return None
    return {"symbol": symbol.upper(), "name": info["name"], "sector": info["sector"]}


def get_all_symbols() -> list[str]:
    """Return all available stock symbols."""
    return list(STOCKS.keys())


def simulate_tick(symbol: str) -> dict:
    """
    Simulate a single price tick for a stock.
    Returns OHLCV-like data point.
    """
    symbol = symbol.upper()
    info = STOCKS.get(symbol)
    if not info:
        info = {"base": 500.0, "sector": "Unknown", "vol": 0.02, "name": symbol}

    price = _init_price(symbol)
    vol = info["vol"]

    # Geometric Brownian Motion step
    dt = 1.0 / 252.0  # one trading day
    drift = -0.0001    # slight mean reversion
    shock = random.gauss(0, 1)
    new_price = price * math.exp((drift - 0.5 * vol**2) * dt + vol * math.sqrt(dt) * shock)

    # Mean reversion toward base
    base = info["base"]
    mean_rev = 0.002
    new_price = new_price + mean_rev * (base - new_price)

    new_price = max(new_price, base * 0.7)  # floor at 70% of base

    _price_state[symbol] = new_price

    # Generate intraday high/low/open
    intra_vol = vol * 0.3
    open_price = price * (1 + random.gauss(0, intra_vol * 0.5))
    high = max(open_price, new_price) * (1 + abs(random.gauss(0, intra_vol)))
    low = min(open_price, new_price) * (1 - abs(random.gauss(0, intra_vol)))

    # Volume: base + random component
    base_volume = random.randint(100000, 5000000)
    vol_spike = 1.0
    # Occasional volume spike
    if random.random() < 0.08:
        vol_spike = random.uniform(2.0, 5.0)
    volume = int(base_volume * vol_spike)

    now = datetime.utcnow().isoformat()

    return {
        "symbol": symbol,
        "price": round(new_price, 2),
        "open": round(open_price, 2),
        "high": round(high, 2),
        "low": round(low, 2),
        "previous_close": round(price, 2),
        "volume": volume,
        "avg_volume_30d": base_volume,
        "change_pct": round(((new_price - price) / price) * 100, 2),
        "timestamp": now,
    }


def get_price_history(symbol: str, periods: int = 20) -> list[dict]:
    """
    Generate simulated historical price data.
    Used by momentum agent for technical analysis.
    """
    symbol = symbol.upper()
    info = STOCKS.get(symbol)
    if not info:
        info = {"base": 500.0, "vol": 0.02}

    base = info["base"]
    vol = info["vol"]
    history = []
    price = base * (1 + random.uniform(-0.05, 0.05))

    for i in range(periods):
        dt = 1.0 / 252.0
        shock = random.gauss(0, 1)
        price = price * math.exp((vol**2 * dt * -0.5) + vol * math.sqrt(dt) * shock)
        volume = random.randint(100000, 3000000)
        ts = (datetime.utcnow() - timedelta(days=periods - i)).isoformat()
        history.append({
            "date": ts,
            "close": round(price, 2),
            "volume": volume,
        })

    return history


def get_sector_distribution(portfolio: dict[str, float]) -> dict[str, float]:
    """
    Calculate sector concentration from portfolio weights.
    Returns Herfindahl-style concentration index components.
    """
    sector_weights: dict[str, float] = {}
    for sym, weight in portfolio.items():
        info = STOCKS.get(sym.upper())
        if info:
            sector = info["sector"]
            sector_weights[sector] = sector_weights.get(sector, 0) + weight
    return sector_weights


def herfindahl_index(sector_weights: dict[str, float]) -> float:
    """Calculate HHI from sector weights (0 to 1 scale, 1 = maximum concentration)."""
    total = sum(sector_weights.values())
    if total == 0:
        return 0.0
    normalized = [w / total for w in sector_weights.values()]
    return round(sum(s**2 for s in normalized), 4)

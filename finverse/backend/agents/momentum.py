"""
FinVerse — Momentum Agent
Rule-based technical analysis + LLM-generated commentary.
Deterministic core (never fails) + natural language layer.
"""
import json
import time
import logging
from datetime import datetime

logger = logging.getLogger("finverse.momentum")

# Standard agent response contract
AGENT_NAME = "momentum_agent"


def _compute_rsi(prices: list[float], period: int = 14) -> float:
    """Compute RSI from a list of closing prices."""
    if len(prices) < period + 1:
        return 50.0  # neutral default

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _detect_ma_crossover(prices: list[float], short: int = 5, long: int = 20) -> str:
    """Detect moving average crossover signal."""
    if len(prices) < long:
        return "neutral"
    sma_short = sum(prices[-short:]) / short
    sma_long = sum(prices[-long:]) / long
    diff_pct = (sma_short - sma_long) / sma_long * 100

    if diff_pct > 0.5:
        return "bullish"
    elif diff_pct < -0.5:
        return "bearish"
    return "neutral"


def _detect_volume_spike(volumes: list[int], threshold: float = 2.0) -> bool:
    """Detect if recent volume is significantly above average."""
    if len(volumes) < 5:
        return False
    avg = sum(volumes[:-1]) / max(len(volumes) - 1, 1)
    latest = volumes[-1]
    return latest > avg * threshold


def _compute_volatility(prices: list[float]) -> float:
    """Annualized volatility from daily returns."""
    if len(prices) < 3:
        return 0.0
    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
    mean_ret = sum(returns) / len(returns)
    var = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
    return (var ** 0.5) * (252 ** 0.5)  # annualize


def analyze(history: list[dict], current_price: float) -> dict:
    """
    Run momentum analysis on historical data.

    Args:
        history: list of {"date": str, "close": float, "volume": int}
        current_price: latest price

    Returns:
        Standard agent JSON contract
    """
    start_time = time.time()

    closes = [h["close"] for h in history]
    volumes = [h["volume"] for h in history]
    closes.append(current_price)

    rsi = _compute_rsi(closes)
    ma_signal = _detect_ma_crossover(closes)
    volume_spike = _detect_volume_spike(volumes)
    volatility = _compute_volatility(closes)

    # Rule-based signal determination
    signals = []
    if rsi > 70:
        signals.append(("bearish", 0.6, f"RSI at {rsi:.1f} indicates overbought conditions"))
    elif rsi > 60:
        signals.append(("bullish", 0.55, f"RSI at {rsi:.1f} shows upward momentum"))
    elif rsi < 30:
        signals.append(("bullish", 0.65, f"RSI at {rsi:.1f} shows oversold — potential bounce"))
    elif rsi < 40:
        signals.append(("bearish", 0.55, f"RSI at {rsi:.1f} shows weakness"))
    else:
        signals.append(("neutral", 0.5, f"RSI at {rsi:.1f} — no strong momentum signal"))

    if ma_signal == "bullish":
        signals.append(("bullish", 0.6, "Short-term MA crosses above long-term MA — uptrend"))
    elif ma_signal == "bearish":
        signals.append(("bearish", 0.6, "Short-term MA crosses below long-term MA — downtrend"))

    if volume_spike:
        signals.append(("bullish" if closes[-1] > closes[-2] else "bearish", 0.7,
                        "Volume spike detected — confirms price move direction"))

    # Aggregate signals
    bullish = sum(1 for s in signals if s[0] == "bullish")
    bearish = sum(1 for s in signals if s[0] == "bearish")

    if bullish > bearish:
        signal = "bullish"
        confidence = min(0.95, sum(s[1] for s in signals if s[0] == "bullish") / bullish)
    elif bearish > bullish:
        signal = "bearish"
        confidence = min(0.95, sum(s[1] for s in signals if s[0] == "bearish") / bearish)
    else:
        signal = "neutral"
        confidence = 0.5

    # Build reasoning
    reasoning_parts = []
    reasoning_parts.append(f"Technical analysis of {len(closes)} data points:")
    for _, conf, reason in signals:
        reasoning_parts.append(f"• {reason}")
    if volume_spike:
        reasoning_parts.append(f"• Volume anomaly: {volumes[-1]:,} vs avg {sum(volumes[:-1])//max(len(volumes)-1,1):,}")
    reasoning_parts.append(f"• Annualized volatility: {volatility*100:.1f}%")

    elapsed_ms = round((time.time() - start_time) * 1000)

    return {
        "agent": AGENT_NAME,
        "signal": signal,
        "confidence": round(confidence, 3),
        "reasoning": " ".join(reasoning_parts),
        "data_sources": ["price_history", "volume_data", "technical_indicators"],
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "rsi": round(rsi, 2),
            "ma_crossover": ma_signal,
            "volume_spike": volume_spike,
            "volatility_annualized": round(volatility * 100, 2),
            "data_points": len(closes),
            "latency_ms": elapsed_ms,
        }
    }

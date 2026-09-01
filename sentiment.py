"""
FinVerse — Sentiment Agent
Classifies news/headline sentiment with confidence scoring.
Uses synthetic headlines for demo, with real LLM integration when available.
"""
import random
import time
import logging
from datetime import datetime

logger = logging.getLogger("finverse.sentiment")

AGENT_NAME = "sentiment_agent"

# Synthetic headline templates per stock — deterministic pool for demo
SYNTHETIC_HEADLINES: dict[str, list[dict]] = {
    "RELIANCE": [
        {"headline": "Reliance Jio 5G subscriber base crosses 500 million milestone", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "Crude oil price surge pressures Reliance petrochemical margins", "source": "Moneycontrol", "sentiment": "negative"},
        {"headline": "Reliance Retail expands to 500 new Tier-3 cities in Q4", "source": "Business Standard", "sentiment": "positive"},
        {"headline": "Jamnagar gigafactory construction ahead of schedule", "source": "Mint", "sentiment": "positive"},
        {"headline": "FII reduces Reliance stake by 0.8% in May selling", "source": "Reuters India", "sentiment": "negative"},
    ],
    "TCS": [
        {"headline": "TCS wins $3.2 billion deal with European banking giant", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "India IT sector faces visa headwinds as US tightens H-1B rules", "source": "Moneycontrol", "sentiment": "negative"},
        {"headline": "TCS GenAI practice expands to 450+ enterprise clients", "source": "Business Standard", "sentiment": "positive"},
        {"headline": "TCS attrition stabilizes at 11.8%, lowest in 18 months", "source": "Mint", "sentiment": "positive"},
        {"headline": "Global IT spending slowdown may impact H2 outlook", "source": "Reuters India", "sentiment": "negative"},
    ],
    "HDFCBANK": [
        {"headline": "HDFC Bank merger integration synergies ahead of schedule", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "NIM compression concerns persist as deposit costs rise", "source": "Moneycontrol", "sentiment": "negative"},
        {"headline": "HDFC Bank leads UPI transaction volume with 5.8 billion monthly", "source": "Business Standard", "sentiment": "positive"},
        {"headline": "RBI policy pause may limit bank NIM expansion", "source": "Mint", "sentiment": "negative"},
        {"headline": "Credit card portfolio crosses 2 crore cards milestone", "source": "Reuters India", "sentiment": "positive"},
    ],
    "INFY": [
        {"headline": "Infosys raises FY2026 guidance to 12-14% CC growth", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "PerfidAI fraud detection platform adopted by 12 major banks", "source": "Moneycontrol", "sentiment": "positive"},
        {"headline": "European banking clients delay discretionary IT spending", "source": "Business Standard", "sentiment": "negative"},
        {"headline": "Infosys Cobalt cloud platform surpasses 45,000 assets", "source": "Mint", "sentiment": "positive"},
        {"headline": "Competitor TCS wins mega deals that Infosys bid for", "source": "Reuters India", "sentiment": "negative"},
    ],
    "SBIN": [
        {"headline": "SBI records highest-ever quarterly profit of ₹21,200 crore", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "GNPA ratio improves to 2.15% as asset quality strengthens", "source": "Moneycontrol", "sentiment": "positive"},
        {"headline": "YONO platform registers 95 million users, digital push accelerates", "source": "Business Standard", "sentiment": "positive"},
        {"headline": "PSU banks face rural credit quality concerns amid monsoon uncertainty", "source": "Mint", "sentiment": "negative"},
        {"headline": "SBI NPA recovery through IBC recovers ₹18,500 crore", "source": "Reuters India", "sentiment": "positive"},
    ],
    "ITC": [
        {"headline": "ITC FMCG EBITDA margins expand 200bps, strong execution", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "Cigarette duty hike in Union Budget may impact core business", "source": "Moneycontrol", "sentiment": "negative"},
        {"headline": "ITC Hotels division posts best-ever year with 40%+ margins", "source": "Business Standard", "sentiment": "positive"},
        {"headline": "Agricultural commodity price volatility impacts sourcing costs", "source": "Mint", "sentiment": "negative"},
        {"headline": "ITC invests ₹5,000 crore in premium personal care expansion", "source": "Reuters India", "sentiment": "positive"},
    ],
    "TATAMOTORS": [
        {"headline": "Tata Motors EV market share crosses 62% in India", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "JLR maintains strong EBIT margin at 8.2% on Range Rover demand", "source": "Moneycontrol", "sentiment": "positive"},
        {"headline": "Commercial vehicle sector faces cyclical downturn headwinds", "source": "Business Standard", "sentiment": "negative"},
        {"headline": "Punch.ev and Nexon.ev dominate India EV charts", "source": "Mint", "sentiment": "positive"},
        {"headline": "Semiconductor supply constraints may impact JLR production", "source": "Reuters India", "sentiment": "negative"},
    ],
    "WIPRO": [
        {"headline": "Wipro AI360 practice serves 200 clients with 1,000+ consultants", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "Operating margins improve to 16.8% from 14.2% YoY", "source": "Moneycontrol", "sentiment": "positive"},
        {"headline": "Wipro Healthcare vertical grows 22%, emerges new engine", "source": "Business Standard", "sentiment": "positive"},
        {"headline": "IT services pricing pressure may impact new deal wins", "source": "Mint", "sentiment": "negative"},
        {"headline": "Wipro completes 3 strategic acquisitions in cloud space", "source": "Reuters India", "sentiment": "positive"},
    ],
    "LT": [
        {"headline": "L&T secures record ₹2.5 lakh crore order book for FY2025", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "Government infrastructure capex boost benefits L&T significantly", "source": "Moneycontrol", "sentiment": "positive"},
        {"headline": "International orders contribute 38% — growing global footprint", "source": "Business Standard", "sentiment": "positive"},
        {"headline": "Raw material cost inflation pressures E&C project margins", "source": "Mint", "sentiment": "negative"},
        {"headline": "Renewable energy order book crosses ₹15,000 crore", "source": "Reuters India", "sentiment": "positive"},
    ],
    "BHARTIARTL": [
        {"headline": "Airtel ARPU crosses ₹245, up 18% YoY sustainably", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "5G coverage expands to 8,000 cities, 4.5M new subscribers", "source": "Moneycontrol", "sentiment": "positive"},
        {"headline": "Telecom tariff hike uncertainty looms over sector outlook", "source": "Business Standard", "sentiment": "negative"},
        {"headline": "Enterprise cybersecurity demand drives 15% growth", "source": "Mint", "sentiment": "positive"},
        {"headline": "Jio price war may force Airtel to increase capex", "source": "Reuters India", "sentiment": "negative"},
    ],
    "ICICIBANK": [
        {"headline": "ICICI Bank Q4 PAT up 18% on strong NII and other income", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "iMobile Pay crosses 35 million users, digital leadership", "source": "Moneycontrol", "sentiment": "positive"},
        {"headline": "Asset quality improves with GNPA at 1.96%, NNPA at 0.42%", "source": "Business Standard", "sentiment": "positive"},
        {"headline": "Unsecured lending norms may constrain retail growth", "source": "Mint", "sentiment": "negative"},
        {"headline": "ICICI Bank CET1 at 19.6% — well-capitalized for growth", "source": "Reuters India", "sentiment": "positive"},
    ],
    "SUNPHARMA": [
        {"headline": "Sun Pharma specialty revenue in US grows 25% YoY", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "Ilumya and Winlevi launches gain market traction", "source": "Moneycontrol", "sentiment": "positive"},
        {"headline": "US FDA inspection concerns may delay new product approvals", "source": "Business Standard", "sentiment": "negative"},
        {"headline": "Domestic formulations maintain 8.5% market share leadership", "source": "Mint", "sentiment": "positive"},
        {"headline": "Biosimilar competition intensifies in key therapeutic areas", "source": "Reuters India", "sentiment": "negative"},
    ],
    "KOTAKBANK": [
        {"headline": "Kotak Bank housing loan book crosses ₹1 lakh crore", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "NIM at 4.32% remains among highest in Indian banking", "source": "Moneycontrol", "sentiment": "positive"},
        {"headline": "Deposit cost pressure may compress margins further", "source": "Business Standard", "sentiment": "negative"},
        {"headline": "Credit card portfolio grows 25% with 1.2M new cards", "source": "Mint", "sentiment": "positive"},
        {"headline": "Kotak General Insurance subsidiary grows 20% YoY", "source": "Reuters India", "sentiment": "positive"},
    ],
    "ADANIENT": [
        {"headline": "Adani Enterprises revenue surges 35% to ₹32,000 crore in Q4", "source": "Economic Times", "sentiment": "positive"},
        {"headline": "Data center business adds 100 MW, 85% utilization", "source": "Moneycontrol", "sentiment": "positive"},
        {"headline": "Deleveraging roadmap targets net debt/EBITDA below 3x by FY2027", "source": "Business Standard", "sentiment": "positive"},
        {"headline": "Adani group faces regulatory scrutiny on related-party deals", "source": "Mint", "sentiment": "negative"},
        {"headline": "Airports business handles 28M passengers, 22% YoY growth", "source": "Reuters India", "sentiment": "positive"},
    ],
}


def _classify_headline(headline_text: str, known_sentiment: str = None) -> dict:
    """
    Classify a headline's sentiment.
    For demo: returns deterministic classification based on synthetic headline tags.
    For production: would call LLM for classification.
    """
    # Keyword-based fallback classification (deterministic)
    positive_words = ["surge", "jump", "gain", "record", "milestone", "strong", "growth",
                      "profit", "breakthrough", "expand", "improve", "lead", "win"]
    negative_words = ["drop", "fall", "decline", "loss", "risk", "crisis", "concern",
                      "slump", "pressur", "headwind", "delay", "cut", "downturn"]
    text_lower = headline_text.lower()

    pos_score = sum(1 for w in positive_words if w in text_lower)
    neg_score = sum(1 for w in negative_words if w in text_lower)

    if known_sentiment == "positive":
        confidence = min(0.88, 0.6 + pos_score * 0.05)
    elif known_sentiment == "negative":
        confidence = min(0.88, 0.6 + neg_score * 0.05)
    else:
        confidence = 0.5

    return {
        "text": headline_text,
        "sentiment": known_sentiment or ("positive" if pos_score >= neg_score else "negative"),
        "confidence": round(confidence, 3),
    }


def analyze(symbol: str, simulate_outage: bool = False) -> dict:
    """
    Run sentiment analysis on recent headlines for a stock.

    Args:
        symbol: stock ticker
        simulate_outage: if True, returns an error response (for degraded-data demo)

    Returns:
        Standard agent JSON contract
    """
    start_time = time.time()

    # Simulated outage mode — key for the degradation demo
    if simulate_outage:
        return {
            "agent": AGENT_NAME,
            "signal": None,
            "confidence": 0.0,
            "reasoning": "SENTIMENT FEED UNAVAILABLE: Unable to retrieve news headlines due to simulated data source outage. Recommendation will rely on remaining agents.",
            "data_sources": [],
            "timestamp": datetime.utcnow().isoformat(),
            "error": True,
            "error_message": "Sentiment data feed outage — source connection failed",
            "metadata": {
                "latency_ms": 0,
                "headlines_analyzed": 0,
                "error_type": "feed_outage",
            }
        }

    headlines = SYNTHETIC_HEADLINES.get(symbol.upper(), [])
    if not headlines:
        return {
            "agent": AGENT_NAME,
            "signal": "neutral",
            "confidence": 0.35,
            "reasoning": f"No recent news found for {symbol}. Insufficient data for sentiment classification.",
            "data_sources": [],
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"latency_ms": round((time.time() - start_time) * 1000), "headlines_analyzed": 0},
        }

    # Classify each headline
    classifications = [_classify_headline(h["headline"], h.get("sentiment")) for h in headlines]

    # Aggregate
    pos = [c for c in classifications if c["sentiment"] == "positive"]
    neg = [c for c in classifications if c["sentiment"] == "negative"]
    total = len(classifications)

    if len(pos) > len(neg):
        signal = "bullish"
        confidence = sum(c["confidence"] for c in pos) / max(len(pos), 1)
    elif len(neg) > len(pos):
        signal = "bearish"
        confidence = sum(c["confidence"] for c in neg) / max(len(neg), 1)
    else:
        signal = "neutral"
        confidence = 0.45

    # Confidence adjusted by coverage
    coverage = total / 5.0  # 5 is ideal headline count
    confidence = round(confidence * min(coverage, 1.0), 3)

    # Build reasoning
    reasoning_parts = [f"Analyzed {total} recent headlines for {symbol}:"]
    for c in classifications:
        emoji = "📈" if c["sentiment"] == "positive" else "📉"
        reasoning_parts.append(f"  {emoji} {c['text'][:80]}... (confidence: {c['confidence']:.2f})")
    reasoning_parts.append(f"Net signal: {len(pos)} positive, {len(neg)} negative → {signal.upper()}")

    elapsed_ms = round((time.time() - start_time) * 1000)

    return {
        "agent": AGENT_NAME,
        "signal": signal,
        "confidence": confidence,
        "reasoning": " ".join(reasoning_parts),
        "data_sources": [h["source"] for h in headlines],
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "headlines_analyzed": total,
            "positive_count": len(pos),
            "negative_count": len(neg),
            "sources": list(set(h["source"] for h in headlines)),
            "latency_ms": elapsed_ms,
        }
    }

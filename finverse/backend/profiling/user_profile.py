"""
FinVerse — User Profiling Engine
Preset personas with stored risk parameters for personalized recommendations.
"""

PERSONAS = {
    "conservative": {
        "id": "conservative",
        "name": "Conservative Investor",
        "risk_tolerance": "conservative",
        "max_volatility": 0.15,
        "max_sector_concentration": 0.25,
        "investment_horizon": "long",
        "max_single_stock_weight": 0.05,
        "stop_loss_pct": 3.0,
        "description": "Capital preservation first. Low tolerance for drawdowns. Prefers stable, large-cap stocks with consistent dividends.",
        "color": "#34d399",  # green
        "icon": "🛡️",
    },
    "balanced": {
        "id": "balanced",
        "name": "Balanced Investor",
        "risk_tolerance": "medium",
        "max_volatility": 0.25,
        "max_sector_concentration": 0.35,
        "investment_horizon": "medium",
        "max_single_stock_weight": 0.10,
        "stop_loss_pct": 5.0,
        "description": "Balances growth and stability. Comfortable with moderate swings for reasonable returns. Diversified portfolio approach.",
        "color": "#4f8cff",  # blue
        "icon": "⚖️",
    },
    "aggressive": {
        "id": "aggressive",
        "name": "Aggressive Growth",
        "risk_tolerance": "aggressive",
        "max_volatility": 0.40,
        "max_sector_concentration": 0.50,
        "investment_horizon": "short",
        "max_single_stock_weight": 0.20,
        "stop_loss_pct": 8.0,
        "description": "Maximizes growth potential. Comfortable with high volatility and concentrated positions. Active trading style.",
        "color": "#ff4d6a",  # red
        "icon": "🚀",
    },
}

# Sample watchlist/portfolio per persona for demo
SAMPLE_PORTFOLIOS = {
    "conservative": {
        "HDFCBANK": 0.15, "ICICIBANK": 0.10, "ITC": 0.10,
        "TCS": 0.10, "HINDUNILVR": 0.10, "BHARTIARTL": 0.08,
        "KOTAKBANK": 0.07, "WIPRO": 0.05, "CASH": 0.25,
    },
    "balanced": {
        "RELIANCE": 0.12, "TCS": 0.12, "HDFCBANK": 0.10,
        "INFY": 0.10, "ITC": 0.08, "BHARTIARTL": 0.08,
        "LT": 0.08, "SBIN": 0.07, "SUNPHARMA": 0.05, "CASH": 0.20,
    },
    "aggressive": {
        "TATAMOTORS": 0.15, "ADANIENT": 0.15, "RELIANCE": 0.12,
        "SBIN": 0.10, "BHARTIARTL": 0.10, "WIPRO": 0.08,
        "LT": 0.08, "SUNPHARMA": 0.07, "INFY": 0.05, "CASH": 0.10,
    },
}

# Default persona for new users
DEFAULT_PERSONA = "balanced"


def get_persona(persona_id: str) -> dict | None:
    """Get a persona by ID."""
    return PERSONAS.get(persona_id.lower())


def get_all_personas() -> list[dict]:
    """Get all available personas."""
    return list(PERSONAS.values())


def get_portfolio(persona_id: str) -> dict[str, float]:
    """Get the sample portfolio for a persona."""
    return SAMPLE_PORTFOLIOS.get(persona_id.lower(), SAMPLE_PORTFOLIOS[DEFAULT_PERSONA])


def compare_recommendations(
    symbol: str,
    price_history: list[dict],
    current_price: float,
    persona_ids: list[str] = None,
) -> list[dict]:
    """
    Generate recommendations for multiple personas on the same stock.
    Used for side-by-side comparison (the "wow" demo moment).
    """
    from agents import orchestrator

    if persona_ids is None:
        persona_ids = list(PERSONAS.keys())

    results = []
    for pid in persona_ids:
        persona = PERSONAS.get(pid, PERSONAS[DEFAULT_PERSONA])
        result = orchestrator.analyze(
            symbol=symbol,
            price_history=price_history,
            current_price=current_price,
            persona=persona,
            simulate_outage=False,
        )
        results.append({
            "persona": persona,
            "recommendation": result["recommendation"],
            "synthesis": result["synthesis"],
            "reasoning_trace": result["reasoning_trace"],
        })

    return results

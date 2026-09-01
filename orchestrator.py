"""
FinVerse — Orchestrator / Synthesis Agent
Runs three agents in parallel, synthesizes outputs, handles degraded data.
"""
import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents import momentum, sentiment, fundamentals

logger = logging.getLogger("finverse.orchestrator")

SIGNAL_WEIGHTS = {"momentum": 0.30, "sentiment": 0.25, "fundamentals": 0.45}
SIGNAL_VALUES = {"bullish": 1.0, "neutral": 0.0, "bearish": -1.0}


def _weighted_score(agent_signals: dict[str, dict]) -> dict:
    """
    Compute weighted recommendation score from available agent signals.
    Weights are rebalanced when agents are unavailable.
    """
    available_agents = {}
    missing_agents = []

    for name, weight_key in [("momentum", "momentum"), ("sentiment", "sentiment"), ("fundamentals", "fundamentals")]:
        result = agent_signals.get(name)
        if result and not result.get("error") and result.get("signal"):
            available_agents[name] = result
        else:
            missing_agents.append(name)

    if not available_agents:
        return {
            "overall_signal": "neutral",
            "overall_confidence": 0.0,
            "weighted_score": 0.0,
            "agents_used": [],
            "agents_missing": missing_agents,
            "rebalanced": False,
        }

    # Rebalance weights
    original_total = sum(SIGNAL_WEIGHTS[a] for a in available_agents)
    rebalanced_weights = {}
    for name in available_agents:
        rebalanced_weights[name] = SIGNAL_WEIGHTS[name] / original_total

    # Compute weighted score
    score = 0.0
    weighted_confidence = 0.0
    for name, agent_result in available_agents.items():
        sv = SIGNAL_VALUES.get(agent_result["signal"], 0.0)
        w = rebalanced_weights[name]
        score += sv * w * agent_result.get("confidence", 0.5)
        weighted_confidence += agent_result.get("confidence", 0.5) * w

    # Determine overall signal
    if score > 0.15:
        overall_signal = "bullish"
    elif score < -0.15:
        overall_signal = "bearish"
    else:
        overall_signal = "neutral"

    # Confidence penalty for missing agents
    confidence_penalty = 1.0 - (len(missing_agents) * 0.15)
    final_confidence = round(weighted_confidence * confidence_penalty, 3)

    return {
        "overall_signal": overall_signal,
        "overall_confidence": min(0.95, final_confidence),
        "weighted_score": round(score, 4),
        "agents_used": list(available_agents.keys()),
        "agents_missing": missing_agents,
        "rebalanced": len(missing_agents) > 0,
    }


def _generate_recommendation(
    symbol: str,
    synthesis: dict,
    agent_signals: dict,
    persona: dict,
) -> str:
    """
    Generate a human-readable recommendation adjusted for the user's persona.
    This is the core personalization output.
    """
    signal = synthesis["overall_signal"]
    confidence = synthesis["overall_confidence"]
    persona_name = persona.get("name", "Balanced")
    risk_level = persona.get("risk_tolerance", "medium")
    max_volatility = persona.get("max_volatility", 0.25)
    horizon = persona.get("investment_horizon", "medium")

    # Get momentum volatility for risk check
    momentum_meta = agent_signals.get("momentum", {}).get("metadata", {})
    volatility = momentum_meta.get("volatility_annualized", 15) / 100

    # Signal text
    if signal == "bullish":
        base_signal = f"Multiple analyst signals converge BULLISH for {symbol} with {confidence:.0%} overall confidence."
    elif signal == "bearish":
        base_signal = f"Multiple analyst signals converge BEARISH for {symbol} with {confidence:.0%} overall confidence."
    else:
        base_signal = f"Analyst signals are MIXED/NEUTRAL for {symbol} with {confidence:.0%} overall confidence."

    # Persona-specific adjustment
    if risk_level == "aggressive":
        if signal == "bullish":
            recommendation = (
                f"{base_signal}\n\n"
                f"Given your AGGRESSIVE risk profile: Momentum and sentiment alignment presents a strong entry opportunity. "
                f"Consider a position sized within your risk band. Volatility at {volatility*100:.1f}% is acceptable for your profile. "
                f"Recommended allocation: 5-8% of portfolio."
            )
        elif signal == "bearish":
            recommendation = (
                f"{base_signal}\n\n"
                f"Given your AGGRESSIVE risk profile: Bearish signals suggest caution, but this could present a short-selling "
                f"or put option opportunity. If holding, consider a stop-loss at 5-8% below current price."
            )
        else:
            recommendation = (
                f"{base_signal}\n\n"
                f"Given your AGGRESSIVE risk profile: No clear directional bias. Consider a small speculative position "
                f"if you have conviction in one particular dimension. Maintain existing allocation otherwise."
            )

    elif risk_level == "conservative":
        if signal == "bullish":
            volatility_high = volatility > max_volatility
            if volatility_high:
                recommendation = (
                    f"{base_signal}\n\n"
                    f"Given your CONSERVATIVE risk profile: Momentum is bullish but volatility ({volatility*100:.1f}%) "
                    f"exceeds your comfort threshold of {max_volatility*100:.0f}%. Suggest a SMALLER starter position "
                    f"(1-2% of portfolio) or WAIT for volatility to subside before entry."
                )
            else:
                recommendation = (
                    f"{base_signal}\n\n"
                    f"Given your CONSERVATIVE risk profile: Bullish alignment supports a measured position. "
                    f"Volatility at {volatility*100:.1f}% is within your risk tolerance. "
                    f"Recommended allocation: 2-3% of portfolio. Consider setting a tight stop-loss."
                )
        elif signal == "bearish":
            recommendation = (
                f"{base_signal}\n\n"
                f"Given your CONSERVATIVE risk profile: Bearish signals are a clear stay-away. "
                f"Do NOT initiate a position. If currently holding, consider reducing exposure. "
                f"Monitor for sentiment improvement before reassessing."
            )
        else:
            recommendation = (
                f"{base_signal}\n\n"
                f"Given your CONSERVATIVE risk profile: Mixed signals warrant patience. "
                f"Do not initiate new positions until consensus forms. "
                f"Focus on your existing portfolio's stability."
            )

    else:  # balanced
        if signal == "bullish":
            recommendation = (
                f"{base_signal}\n\n"
                f"Given your BALANCED risk profile: Bullish alignment supports a moderate position. "
                f"Recommended allocation: 3-5% of portfolio. Volatility at {volatility*100:.1f}% — "
                f"set a stop-loss at 4-6% below entry."
            )
        elif signal == "bearish":
            recommendation = (
                f"{base_signal}\n\n"
                f"Given your BALANCED risk profile: Reduce exposure if overweight in {symbol}. "
                f"Avoid new entries until bearish pressure eases. Revisit in 1-2 weeks."
            )
        else:
            recommendation = (
                f"{base_signal}\n\n"
                f"Given your BALANCED risk profile: Mixed signals suggest holding current allocation. "
                f"Do not add to position until clearer signal emerges."
            )

    return recommendation


def analyze(
    symbol: str,
    price_history: list[dict],
    current_price: float,
    persona: dict,
    simulate_outage: bool = False,
) -> dict:
    """
    Run all three agents in parallel, synthesize results.

    Args:
        symbol: stock ticker
        price_history: historical OHLCV data
        current_price: latest price
        persona: user profile parameters
        simulate_outage: if True, kills sentiment agent

    Returns:
        Full synthesis result with recommendation, reasoning trace, citations
    """
    start_time = time.time()

    # Run agents in parallel
    agent_results = {}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}

        futures["momentum"] = executor.submit(
            momentum.analyze, price_history, current_price
        )
        futures["sentiment"] = executor.submit(
            sentiment.analyze, symbol, simulate_outage
        )
        futures["fundamentals"] = executor.submit(
            fundamentals.analyze, symbol
        )

        for name, future in futures.items():
            try:
                agent_results[name] = future.result(timeout=30)
            except Exception as e:
                logger.error(f"Agent {name} failed: {e}")
                agent_results[name] = {
                    "agent": f"{name}_agent",
                    "signal": None,
                    "confidence": 0.0,
                    "reasoning": f"Agent error: {str(e)}",
                    "data_sources": [],
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": True,
                    "error_message": str(e),
                }

    # Synthesize
    synthesis = _weighted_score(agent_results)
    recommendation = _generate_recommendation(symbol, synthesis, agent_results, persona)

    # Build reasoning trace — numbered steps
    reasoning_trace = []
    step_num = 1

    if "momentum" in agent_results and not agent_results["momentum"].get("error"):
        reasoning_trace.append({
            "step": step_num,
            "agent": "Momentum Agent",
            "finding": f"Technical analysis yielded a {agent_results['momentum']['signal'].upper()} signal "
                       f"with {agent_results['momentum']['confidence']:.0%} confidence. "
                       f"{agent_results['momentum']['reasoning'][:150]}",
            "signal": agent_results["momentum"]["signal"],
            "confidence": agent_results["momentum"]["confidence"],
        })
        step_num += 1
    else:
        error_msg = agent_results.get("momentum", {}).get("error_message", "unknown error")
        reasoning_trace.append({
            "step": step_num,
            "agent": "Momentum Agent",
            "finding": f"Agent unavailable: {error_msg}",
            "signal": "unavailable",
            "confidence": 0,
        })
        step_num += 1

    if "sentiment" in agent_results and not agent_results["sentiment"].get("error"):
        reasoning_trace.append({
            "step": step_num,
            "agent": "Sentiment Agent",
            "finding": f"News sentiment analysis yielded a {agent_results['sentiment']['signal'].upper()} signal "
                       f"with {agent_results['sentiment']['confidence']:.0%} confidence.",
            "signal": agent_results["sentiment"]["signal"],
            "confidence": agent_results["sentiment"]["confidence"],
        })
        step_num += 1
    else:
        error_msg = agent_results.get("sentiment", {}).get("error_message", "feed unavailable")
        reasoning_trace.append({
            "step": step_num,
            "agent": "Sentiment Agent",
            "finding": f"⚠️ SENTIMENT DATA UNAVAILABLE: {error_msg}. "
                       f"Recommendation based on {len(agent_results) - 1} remaining agents, confidence adjusted down.",
            "signal": "unavailable",
            "confidence": 0,
        })
        step_num += 1

    if "fundamentals" in agent_results and not agent_results["fundamentals"].get("error"):
        fund = agent_results["fundamentals"]
        citation_summary = ""
        if "citations" in fund and fund["citations"]:
            citation_summary = f" Retrieved {len(fund['citations'])} filing excerpts with citations."
        reasoning_trace.append({
            "step": step_num,
            "agent": "Fundamentals/RAG Agent",
            "finding": f"Corporate filing analysis yielded a {fund['signal'].upper()} signal "
                       f"with {fund['confidence']:.0%} confidence.{citation_summary}",
            "signal": fund["signal"],
            "confidence": fund["confidence"],
        })
        step_num += 1

    # Final synthesis step
    reasoning_trace.append({
        "step": step_num,
        "agent": "Orchestrator",
        "finding": f"Synthesized {len(synthesis['agents_used'])} agent signals "
                   f"({'rebalanced weights' if synthesis['rebalanced'] else 'standard weights'}). "
                   f"Final signal: {synthesis['overall_signal'].upper()} at {synthesis['overall_confidence']:.0%} confidence.",
        "signal": synthesis["overall_signal"],
        "confidence": synthesis["overall_confidence"],
    })

    # Get citations from fundamentals agent
    citations = agent_results.get("fundamentals", {}).get("citations", [])

    elapsed_ms = round((time.time() - start_time) * 1000)

    return {
        "symbol": symbol,
        "current_price": current_price,
        "timestamp": datetime.utcnow().isoformat(),
        "agent_results": {
            "momentum": agent_results.get("momentum"),
            "sentiment": agent_results.get("sentiment"),
            "fundamentals": agent_results.get("fundamentals"),
        },
        "synthesis": synthesis,
        "recommendation": recommendation,
        "reasoning_trace": reasoning_trace,
        "citations": citations,
        "persona_applied": persona,
        "total_latency_ms": elapsed_ms,
    }

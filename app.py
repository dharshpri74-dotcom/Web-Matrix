"""
FinVerse — FastAPI Backend
Multi-analyst stock research platform.
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import init_db, log_session, log_metric, get_metrics_summary, get_recent_sessions
from data.mock_generator import get_all_symbols, simulate_tick, get_price_history, get_stock_info, STOCKS
from profiling.user_profile import get_persona, get_all_personas, get_portfolio
from agents import orchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("finverse")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("🚀 FinVerse started")
    yield
    logger.info("FinVerse stopped")


app = FastAPI(title="FinVerse", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Models ──────────────────────────────────────

class AnalysisRequest(BaseModel):
    symbol: str
    persona: str = "balanced"
    simulate_outage: bool = False


class PersonaComparisonRequest(BaseModel):
    symbol: str


# ── API Routes ──────────────────────────────────────────

@app.get("/api/stocks")
async def list_stocks():
    """List all available stocks with current simulated prices."""
    stocks = []
    for sym, info in STOCKS.items():
        tick = simulate_tick(sym)
        stocks.append({
            "symbol": sym,
            "name": info["name"],
            "sector": info["sector"],
            "price": tick["price"],
            "change_pct": tick["change_pct"],
        })
    return {"stocks": stocks}


@app.get("/api/stocks/{symbol}")
async def get_stock(symbol: str):
    """Get detailed stock info."""
    symbol = symbol.upper()
    info = get_stock_info(symbol)
    if not info:
        raise HTTPException(404, f"Stock {symbol} not found")
    tick = simulate_tick(symbol)
    history = get_price_history(symbol)
    return {
        "info": info,
        "current": tick,
        "history": history,
    }


@app.post("/api/analyze")
async def analyze_stock(req: AnalysisRequest):
    """
    Run full multi-agent analysis on a stock.
    This is the core endpoint — fires 3 agents in parallel, synthesizes.
    """
    symbol = req.symbol.upper()
    info = get_stock_info(symbol)
    if not info:
        raise HTTPException(404, f"Stock {symbol} not found")

    persona = get_persona(req.persona)
    if not persona:
        raise HTTPException(400, f"Unknown persona: {req.persona}")

    # Get price data
    tick = simulate_tick(symbol)
    history = get_price_history(symbol)

    # Run orchestrator (parallel agent execution + synthesis)
    result = orchestrator.analyze(
        symbol=symbol,
        price_history=history,
        current_price=tick["price"],
        persona=persona,
        simulate_outage=req.simulate_outage,
    )
    result["simulate_outage"] = req.simulate_outage

    # Log to database
    session_id = log_session(result)
    result["session_id"] = session_id

    # Log agent latency metrics
    for agent_name in ["momentum", "sentiment", "fundamentals"]:
        agent_data = result.get("agent_results", {}).get(agent_name, {})
        if agent_data and not agent_data.get("error"):
            latency = agent_data.get("metadata", {}).get("latency_ms", 0) if isinstance(agent_data.get("metadata"), dict) else 0
            log_metric(f"agent_latency_{agent_name}", latency, {"symbol": symbol, "session_id": session_id})

    logger.info(f"✅ Analysis complete for {symbol} ({req.persona}): {result['synthesis']['overall_signal']}")
    return result


@app.post("/api/compare")
async def compare_personas(req: PersonaComparisonRequest):
    """
    Compare recommendations across all personas for the same stock.
    This is the side-by-side "wow" demo moment.
    """
    symbol = req.symbol.upper()
    info = get_stock_info(symbol)
    if not info:
        raise HTTPException(404, f"Stock {symbol} not found")

    tick = simulate_tick(symbol)
    history = get_price_history(symbol)
    personas = get_all_personas()

    comparisons = []
    for persona in personas:
        result = orchestrator.analyze(
            symbol=symbol,
            price_history=history,
            current_price=tick["price"],
            persona=persona,
            simulate_outage=False,
        )
        log_session(result)
        comparisons.append({
            "persona": persona,
            "recommendation": result["recommendation"],
            "synthesis": result["synthesis"],
            "reasoning_trace": result["reasoning_trace"],
            "citations": result["citations"],
        })

    return {
        "symbol": symbol,
        "current_price": tick["price"],
        "comparisons": comparisons,
    }


@app.get("/api/personas")
async def list_personas():
    """Get all available user personas."""
    return {"personas": get_all_personas()}


@app.get("/api/personas/{persona_id}/portfolio")
async def get_persona_portfolio(persona_id: str):
    """Get the sample portfolio for a persona."""
    portfolio = get_portfolio(persona_id)
    persona = get_persona(persona_id)
    if not persona:
        raise HTTPException(404, f"Persona {persona_id} not found")
    return {
        "persona": persona,
        "portfolio": [
            {"symbol": sym, "weight": round(w, 2), "sector": STOCKS.get(sym, {}).get("sector", "N/A")}
            for sym, w in portfolio.items()
        ],
    }


@app.get("/api/metrics")
async def get_metrics():
    """Get performance metrics and analytics."""
    return get_metrics_summary()


@app.get("/api/metrics/recent")
async def get_recent_analyses():
    """Get recent analysis sessions."""
    return {"sessions": get_recent_sessions(50)}


# ── Serve Frontend ───────────────────────────────────────

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

if os.path.exists(os.path.join(frontend_dir, "static")):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

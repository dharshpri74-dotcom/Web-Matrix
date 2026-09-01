# FinVerse


> "FinVerse gives a first-time retail investor the same multi-analyst research process a hedge fund runs — fully cited, fully explainable, personalized to their risk profile."

---

## Architecture

```
                    ┌─────────────────────────┐
                    │      USER INTERFACE      │
                    │  (React/HTML dashboard)  │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   ORCHESTRATOR AGENT      │
                    │  - dispatches parallel    │
                    │    agent tasks            │
                    │  - handles degraded data  │
                    │  - synthesizes final      │
                    │    recommendation         │
                    └──┬──────────┬──────────┬──┘
         ┌─────────────┘          │          └─────────────┐
         ▼                        ▼                        ▼
┌───────────────────┐  ┌──────────────────────┐  ┌────────────────────┐
│ MOMENTUM AGENT     │  │ SENTIMENT AGENT       │  │ FUNDAMENTALS/RAG   │
│ - price momentum   │  │ - news/social signal  │  │ AGENT               │
│ - volume anomaly   │  │ - confidence score    │  │ - queries vector DB │
│ - technical rules  │  │                        │  │ - cites filings     │
└─────────┬──────────┘  └──────────┬─────────────┘  └──────────┬──────────┘
         │                        │                            │
         └────────────┬───────────┴────────────────────────────┘
                       ▼
            ┌─────────────────────┐
            │  USER PROFILE ENGINE │
            │  - risk tolerance    │
            │  - portfolio state   │
            │  - reweights outputs │
            └──────────┬───────────┘
                       ▼
            ┌─────────────────────┐
            │  SYNTHESIZED OUTPUT  │
            │  + reasoning trace   │
            │  + citations         │
            └──────────┬───────────┘
                       ▼
            ┌─────────────────────┐
            │  LOGGING / METRICS   │
            │  (SQLite)            │
            └─────────────────────┘
```

## Features

- **3 Independent Agents** running in parallel:
  - **Momentum Agent** — RSI, moving average crossover, volume spike detection
  - **Sentiment Agent** — News headline classification with confidence scoring
  - **Fundamentals/RAG Agent** — Queries filing corpus with source-level citations
- **Orchestrator** — Synthesizes 3 signals, resolves conflicts, rebalances weights
- **3 User Personas** — Conservative / Balanced / Aggressive produce different recommendations on the same stock
- **Degraded-Data Handling** — "Simulate Feed Outage" button kills sentiment agent, shows confidence adjustment
- **Reasoning Trace** — Numbered step-by-step explanation of how the recommendation was formed
- **Source Citations** — Clickable filing excerpts with relevance scores
- **Performance Metrics** — Agent latency, signal distribution, outage impact stats

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| Backend | FastAPI + Python | Async support, fast to build |
| Agent Orchestration | ThreadPoolExecutor (parallel) | Maps to "3 agents in parallel" requirement |
| Vector DB | ChromaDB (optional) | Zero-config RAG — works without it via built-in fallback |
| Database | SQLite | Zero-config persistence for logging/metrics |
| Frontend | Vanilla HTML/JS/CSS | Single file, no build step, instant demo |
| Market Data | Mock generator (GBM simulation) | Realistic OHLCV without paid API access |
| Corpus | 14 synthetic SEBI filings | Controllable, guarantees good RAG demo hits |

## Quick Start

```bash
# Install dependencies
pip install fastapi uvicorn numpy pandas

# Optional: install ChromaDB for RAG (may need network access)
pip install chromadb

# Run the app
python start.py
```

Then open **http://127.0.0.1:8000** in your browser.

## Project Structure

```
finverse/
├── start.py                    # One-command launcher
├── requirements.txt            # Python dependencies
├── README.md
├── frontend/
│   └── index.html             # Full SPA dashboard
└── backend/
    ├── app.py                 # FastAPI server (8 endpoints)
    ├── models.py              # SQLite logging + metrics
    ├── agents/
    │   ├── momentum.py        # Technical analysis (RSI, MA, volume)
    │   ├── sentiment.py       # News headline classification
    │   ├── fundamentals.py    # RAG over filing corpus
    │   └── orchestrator.py    # Parallel execution + synthesis
    ├── data/
    │   ├── mock_generator.py  # 15 NSE stocks, GBM price simulation
    │   ├── generate_corpus.py # 14 synthetic SEBI filings
    │   └── corpus_ingest.py   # ChromaDB chunking + embedding
    └── profiling/
        └── user_profile.py    # 3 personas with risk parameters
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stocks` | List all stocks with simulated prices |
| GET | `/api/stocks/{symbol}` | Detailed stock info + history |
| POST | `/api/analyze` | Run full multi-agent analysis |
| POST | `/api/compare` | Compare all 3 personas on same stock |
| GET | `/api/personas` | List available user personas |
| GET | `/api/personas/{id}/portfolio` | Get persona sample portfolio |
| GET | `/api/metrics` | Performance metrics summary |
| GET | `/api/metrics/recent` | Recent analysis sessions |

## Agent JSON Contract

Every agent returns a strict JSON contract:

```json
{
  "agent": "momentum_agent",
  "signal": "bullish | bearish | neutral",
  "confidence": 0.0-1.0,
  "reasoning": "short natural language justification",
  "data_sources": ["source1", "source2"],
  "timestamp": "..."
}
```

## What's Simulated vs. Real

| Component | Status | Notes |
|-----------|--------|-------|
| Stock prices | Simulated (GBM) | Realistic random walk, no paid API needed |
| News headlines | Synthetic | Pre-generated, deterministic for demo |
| Filing corpus | Synthetic | 14 SEBI-style filings, realistic content |
| RAG retrieval | Real (ChromaDB) | Optional — falls back to built-in data |
| Agent logic | Real | Deterministic analysis, no LLM dependency |
| Personalization | Real | Different outputs per persona, verifiable |
| Metrics logging | Real | SQLite, persistent across sessions |

> Honesty note: We are upfront about what's mocked vs. real. Over-claiming live NSE integration we don't have would lose judge trust.

## Demo Script (2 minutes)

1. **Open dashboard** — stocks live, signal badges visible (10s)
2. **Click a stock** — 3 agents fire, synthesis with reasoning trace (30s)
3. **Click a citation** — show RAG-retrieved filing chunk (15s)
4. **Switch persona** — Conservative → Aggressive, different recommendation (20s) ⭐ *wow moment*
5. **Hit "Simulate Feed Outage"** — graceful degradation, confidence drops (20s)
6. **Show metrics panel** — latency, signal distribution (10s)
7. **Close with one-liner pitch** (10s)

## License

MIT

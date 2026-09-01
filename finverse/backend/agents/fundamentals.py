"""
FinVerse — Fundamentals/RAG Agent
Queries ChromaDB corpus for filing chunks, synthesizes answers with citations.
"""
import os
import time
import logging
from datetime import datetime

logger = logging.getLogger("finverse.fundamentals")

AGENT_NAME = "fundamentals_agent"
CHROMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chroma_data"))

# Document IDs mapped to stocks for synthetic corpus
DOC_MAPPING = {
    "RELIANCE":  ["SEBI-RELIANCE-2025-Q4"],
    "TCS":       ["SEBI-TCS-2025-Q4"],
    "HDFCBANK":  ["SEBI-HDFCBANK-2025-Q4"],
    "INFY":      ["SEBI-INFY-2025-Q4"],
    "SBIN":      ["SEBI-SBIN-2025-Q4"],
    "ITC":       ["SEBI-ITC-2025-Q4"],
    "TATAMOTORS":["SEBI-TATAMOTORS-2025-Q4"],
    "WIPRO":     ["SEBI-WIPRO-2025-Q4"],
    "LT":        ["SEBI-LT-2025-Q4"],
    "BHARTIARTL":["SEBI-BHARTIARTL-2025-Q4"],
    "ICICIBANK": ["SEBI-ICICIBANK-2025-Q4"],
    "SUNPHARMA": ["SEBI-SUNPHARMA-2025-Q4"],
    "KOTAKBANK": ["SEBI-KOTAKBANK-2025-Q4"],
    "ADANIENT":  ["SEBI-ADANIENT-2025-Q4"],
}

# Fallback text if ChromaDB unavailable
FALLBACK_FILINGS: dict[str, str] = {
    "RELIANCE": "Reliance Industries Q4 FY2025: Revenue growth driven by Jio (500M subscribers, ARPU ₹192) and Retail (18% YoY growth). EBITDA ₹62,100 crore (+12% YoY). New energy gigafactory ahead of schedule. CAPEX guidance ₹1.2 lakh crore for FY2026. Debt/equity 0.42.",
    "TCS": "TCS Q4 FY2025: Revenue +14.2% in constant currency. Deal TCV $12.2B. BFSI vertical +16%. EBIT margin 27.8% (up from 25.3%). 28K associates added net. AI/GenAI practice spans 450+ clients.",
    "HDFCBANK": "HDFC Bank Q4 FY2025: Post-merger stronger. Deposits +15.6% to ₹24.5 lakh crore. NIM 3.44%. GNPA 1.24%, NNPA 0.33%. 4.2M new digital customers. CET1 ratio 19.2%. Recommended dividend ₹22/share.",
    "INFY": "Infosys Q4 FY2025: CC revenue +11.8%. TCV $8.1B including 5 mega deals. Raising FY26 guidance to 12-14% CC. Operating margin guidance 26-28%. FCF conversion 92%.",
    "SBIN": "SBI Q4 FY2025: PAT ₹21,200 crore (+24% YoY). Full-year PAT crossed ₹70,000 crore. Credit growth 16.2%. NIM 3.47%. GNPA 2.15%. YONO 95M users.",
    "ITC": "ITC FY2025: FMCG revenue ₹21,000 crore (+12%). Hotels revenue ₹9,200 crore (40%+ margins). Agriculture ₹22,000 crore. Carbon positive 19th consecutive year. Investing ₹5,000 crore in new FMCG categories.",
    "TATAMOTORS": "Tata Motors Q4 FY2025: Revenue ₹1.2 lakh crore (+13%). JLR EBIT 8.2%. Domestic EV market share 62%. Sold 28K EVs in Q4 (+45% YoY). CV market share 38%. Target zero net debt by FY2027.",
    "WIPRO": "Wipro Q4 FY2025: Revenue ₹23,200 crore (+10.5% CC). Top 10 clients +18%. BFSI +14%, Healthcare +22%. EBIT margin 16.8% (from 14.2%). Guiding 17-19% margins for FY26.",
    "LT": "L&T Q4 FY2025: Record order intake ₹2.5 lakh crore. Order book ₹4.8 lakh crore. EBITDA margin 12.5%. International orders 38%. Renewable energy orders ₹15,000 crore.",
    "BHARTIARTL": "Bharti Airtel Q4 FY2025: India revenue +12%. ARPU ₹245 (+18%). 5G in 8,000 cities. FCF ₹18,500 crore. Net debt/EBITDA 2.5x. ARPU target ₹300 in 18 months.",
    "ICICIBANK": "ICICI Bank Q4 FY2025: PAT ₹12,800 crore (+18%). NII +14%, Other Income +22%. GNPA 1.96%. CET1 19.6%. iMobile Pay 35M users.",
    "SUNPHARMA": "Sun Pharma Q4 FY2025: Revenue ₹12,600 crore (+11%). US specialty +25%. Domestic leadership at 8.5% share. EBITDA margin 26.2%. 15 ANDAs pending. R&D ₹850 crore.",
    "KOTAKBANK": "Kotak Bank Q4 FY2025: PAT ₹5,200 crore (+16%). Deposits +14%. CASA 42%. Housing loans ₹1 lakh crore. NIM 4.32%. GNPA 1.65%. Credit cards +25%.",
    "ADANIENT": "Adani Enterprises Q4 FY2025: Revenue ₹32,000 crore (+35%). New energy PPAs ₹15,000 crore. Data centers 100 MW at 85% utilization. Airports 28M passengers (+22%). Net debt/EBITDA 3.8x.",
}


def _query_chromadb(query_text: str, symbol: str, top_k: int = 4) -> list[dict]:
    """Query ChromaDB for relevant document chunks."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection("finverse_corpus")

        # Filter by relevant document IDs
        doc_ids = DOC_MAPPING.get(symbol.upper(), [])
        if doc_ids:
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where={"doc_id": {"$in": doc_ids}},
            )
        else:
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k,
            )

        chunks = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0
                chunks.append({
                    "text": doc,
                    "doc_id": meta.get("doc_id", "unknown"),
                    "title": meta.get("title", "Unknown Document"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "relevance_score": round(1 - distance, 3),
                })
        return chunks
    except Exception as e:
        logger.warning(f"ChromaDB query failed: {e}")
        return []


def analyze(symbol: str) -> dict:
    """
    Run fundamentals analysis using RAG over filing corpus.

    Returns:
        Standard agent JSON contract with citations
    """
    start_time = time.time()
    symbol = symbol.upper()

    # Query the corpus
    query = f"Financial performance, earnings, revenue growth, profitability metrics for {symbol}"
    chunks = _query_chromadb(query, symbol)

    # Fallback to static data if no chunks found
    if not chunks:
        fallback = FALLBACK_FILINGS.get(symbol)
        if fallback:
            chunks = [{
                "text": fallback,
                "doc_id": DOC_MAPPING.get(symbol, ["synthetic"])[0] if DOC_MAPPING.get(symbol) else "synthetic",
                "title": f"{symbol} Earnings Summary (Synthetic)",
                "chunk_index": 0,
                "relevance_score": 0.85,
            }]

    # Build citations
    citations = []
    for i, chunk in enumerate(chunks):
        citations.append({
            "citation_id": i + 1,
            "doc_id": chunk["doc_id"],
            "title": chunk["title"],
            "excerpt": chunk["text"][:200] + ("..." if len(chunk["text"]) > 200 else ""),
            "relevance_score": chunk.get("relevance_score", 0.8),
        })

    # Extract key metrics from chunks for signal determination
    combined_text = " ".join(c["text"] for c in chunks).lower()
    positive_indicators = 0
    negative_indicators = 0

    growth_words = ["growth", "increase", "up", "surpass", "record", "improve", "strong", "expand", "ahead"]
    risk_words = ["pressure", "decline", "risk", "concern", "down", "loss", "slowdown", "headwind"]

    for w in growth_words:
        if w in combined_text:
            positive_indicators += 1
    for w in risk_words:
        if w in combined_text:
            negative_indicators += 1

    if positive_indicators > negative_indicators + 2:
        signal = "bullish"
        confidence = min(0.9, 0.6 + (positive_indicators - negative_indicators) * 0.05)
    elif negative_indicators > positive_indicators + 2:
        signal = "bearish"
        confidence = min(0.9, 0.6 + (negative_indicators - positive_indicators) * 0.05)
    else:
        signal = "neutral"
        confidence = 0.5

    # Build reasoning with explicit citations
    reasoning_parts = [f"Fundamentals analysis for {symbol} based on {len(chunks)} filing excerpts:"]
    for c in citations:
        reasoning_parts.append(
            f"  [Source {c['citation_id']}] {c['title']}: {c['excerpt']}"
        )
    reasoning_parts.append(f"Fundamental signal: {signal.upper()} (confidence: {confidence:.2f})")

    elapsed_ms = round((time.time() - start_time) * 1000)

    return {
        "agent": AGENT_NAME,
        "signal": signal,
        "confidence": round(confidence, 3),
        "reasoning": " ".join(reasoning_parts),
        "data_sources": list(set(c["doc_id"] for c in citations)),
        "timestamp": datetime.utcnow().isoformat(),
        "citations": citations,
        "metadata": {
            "chunks_retrieved": len(chunks),
            "corpus_documents": len(set(c["doc_id"] for c in citations)),
            "avg_relevance": round(sum(c["relevance_score"] for c in citations) / max(len(citations), 1), 3),
            "latency_ms": elapsed_ms,
        }
    }

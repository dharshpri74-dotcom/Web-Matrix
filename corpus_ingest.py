"""
FinVerse — Corpus Ingestion into ChromaDB
Splits synthetic filings into chunks and embeds them for RAG.
"""
import os
import re
import logging

logger = logging.getLogger("finverse.corpus")

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "corpus")
CHUNK_SIZE = 500  # characters
CHUNK_OVERLAP = 100


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Split text into overlapping chunks."""
    chunks = []
    # Split by paragraphs first, then chunk long paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk = (current_chunk + "\n\n" + para).strip()
        else:
            if current_chunk:
                chunks.append({"text": current_chunk})
            if len(para) > chunk_size:
                # Split long paragraphs by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current_chunk = ""
                for sent in sentences:
                    if len(current_chunk) + len(sent) + 1 <= chunk_size:
                        current_chunk = (current_chunk + " " + sent).strip()
                    else:
                        if current_chunk:
                            chunks.append({"text": current_chunk})
                        current_chunk = sent
            else:
                current_chunk = para

    if current_chunk:
        chunks.append({"text": current_chunk})

    return chunks


def ingest_corpus():
    """Ingest all corpus files into ChromaDB."""
    try:
        import chromadb
    except ImportError:
        logger.warning("chromadb not installed — RAG agent will use fallback")
        return

    # Initialize ChromaDB
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_data")
    client = chromadb.PersistentClient(path=os.path.abspath(db_path))

    # Check if already ingested
    try:
        collection = client.get_collection("finverse_corpus")
        count = collection.count()
        if count > 10:
            logger.info(f"Corpus already ingested ({count} chunks). Skipping.")
            return
    except Exception:
        collection = client.get_or_create_collection(
            "finverse_corpus",
            metadata={"hnsw:space": "cosine"}
        )

    # Read and chunk all filings
    if not os.path.exists(CORPUS_DIR):
        logger.warning(f"Corpus directory not found: {CORPUS_DIR}")
        return

    doc_count = 0
    for filename in sorted(os.listdir(CORPUS_DIR)):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(CORPUS_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract document ID from first line
        doc_id_match = re.search(r"DOCUMENT ID:\s*(.+)", content)
        doc_id = doc_id_match.group(1).strip() if doc_id_match else filename

        title_match = re.search(r"TITLE:\s*(.+)", content)
        title = title_match.group(1).strip() if title_match else filename

        # Skip header lines
        body_start = content.find("=" * 60)
        if body_start >= 0:
            content = content[body_start + 60:].strip()

        chunks = _chunk_text(content)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}__chunk_{i}"
            metadata = {
                "doc_id": doc_id,
                "title": title,
                "chunk_index": i,
                "source_file": filename,
            }
            collection.upsert(
                ids=[chunk_id],
                documents=[chunk["text"]],
                metadatas=[metadata],
            )

        doc_count += 1
        logger.info(f"  Ingested {filename}: {len(chunks)} chunks")

    total = collection.count()
    logger.info(f"Corpus ingestion complete: {doc_count} documents, {total} total chunks")


if __name__ == "__main__":
    from backend.data.generate_corpus import generate_all_filings
    generate_all_filings()
    ingest_corpus()

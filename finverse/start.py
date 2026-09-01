"""
FinVerse — Quick start script.
Run: python start.py
"""
import subprocess, sys, os

def ensure_deps():
    try:
        import fastapi, chromadb
    except ImportError:
        print("Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r",
                               os.path.join(os.path.dirname(__file__), "requirements.txt")])

if __name__ == "__main__":
    ensure_deps()
    # Generate synthetic filings corpus
    from backend.data.generate_corpus import generate_all_filings
    generate_all_filings()
    # Ingest corpus into ChromaDB
    from backend.data.corpus_ingest import ingest_corpus
    ingest_corpus()
    # Launch server
    os.chdir(os.path.join(os.path.dirname(__file__), "backend"))
    import uvicorn
    print("\n🚀 FinVerse starting at http://127.0.0.1:8000\n")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)

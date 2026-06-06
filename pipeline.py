"""
Run the full pipeline: fetch → consolidate → index
"""
from app.fetcher import fetch_all
from app.consolidator import consolidate
from app.indexer import index

if __name__ == "__main__":
    print("=== Step 1: Fetching OneNote pages ===")
    fetch_all()
    print("\n=== Step 2: Consolidating duplicates ===")
    consolidate()
    print("\n=== Step 3: Indexing into ChromaDB ===")
    index()
    print("\n✅ Pipeline complete. Run: uvicorn app.api:app --reload")

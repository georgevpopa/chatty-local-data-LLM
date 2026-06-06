"""
Ingests consolidated pages into ChromaDB using Ollama embeddings.
"""
import os
import json
import pathlib
import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "mistral")
CONSOLIDATED_DIR = pathlib.Path("data/consolidated")
CHUNK_SIZE = 800  # characters per chunk


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """Split text into overlapping chunks."""
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        start += size - 100  # 100-char overlap
    return chunks


def index():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = OllamaEmbeddingFunction(url=f"{OLLAMA_URL}/api/embeddings", model_name=MODEL)
    collection = client.get_or_create_collection("onenote_faq", embedding_function=ef)

    pages = [json.loads(p.read_text(encoding="utf-8")) for p in CONSOLIDATED_DIR.glob("*.json")]
    print(f"Indexing {len(pages)} consolidated pages...")

    total_chunks = 0
    for page in pages:
        chunks = chunk_text(page["text"])
        for i, chunk in enumerate(chunks):
            doc_id = f"{page['id']}_chunk{i}"
            # Skip if already indexed
            if collection.get(ids=[doc_id])["ids"]:
                continue
            collection.add(
                ids=[doc_id],
                documents=[chunk],
                metadatas=[{
                    "title": page["title"],
                    "notebook": page["notebook"],
                    "section": page["section"],
                    "page_id": page["id"],
                    "chunk": i,
                }],
            )
            total_chunks += 1
        print(f"  {page['title']} → {len(chunks)} chunks")

    print(f"\nDone. {total_chunks} chunks indexed into ChromaDB at {CHROMA_PATH}")


if __name__ == "__main__":
    index()

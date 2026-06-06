"""
RAG query layer: retrieves relevant chunks from ChromaDB and generates an answer with Ollama.
"""
import os
import chromadb
import ollama
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "mistral")
TOP_K = 5

RAG_PROMPT = """You are a helpful technical assistant for a network/IT operations team.
Answer the question below using ONLY the provided context. Be concise and precise.
If the context doesn't contain enough information, say so.

Context:
{context}

Question: {question}
"""

_collection = None


def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        ef = OllamaEmbeddingFunction(url=f"{OLLAMA_URL}/api/embeddings", model_name=MODEL)
        _collection = client.get_collection("onenote_faq", embedding_function=ef)
    return _collection


def query(question: str) -> dict:
    results = get_collection().query(query_texts=[question], n_results=TOP_K)

    chunks = results["documents"][0]
    metas = results["metadatas"][0]

    context = "\n\n---\n\n".join(
        f"[{m['notebook']} / {m['section']} / {m['title']}]\n{doc}"
        for doc, m in zip(chunks, metas)
    )

    prompt = RAG_PROMPT.format(context=context, question=question)
    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])

    sources = [
        {"title": m["title"], "notebook": m["notebook"], "section": m["section"]}
        for m in metas
    ]
    # Deduplicate sources
    seen, unique_sources = set(), []
    for s in sources:
        key = (s["notebook"], s["section"], s["title"])
        if key not in seen:
            seen.add(key)
            unique_sources.append(s)

    return {
        "answer": response["message"]["content"].strip(),
        "sources": unique_sources,
    }

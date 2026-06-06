"""
Groups similar pages using TF-IDF cosine similarity, then consolidates each group
into a single clean document using Ollama.
"""
import os
import json
import pathlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import ollama
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "mistral")
THRESHOLD = float(os.getenv("CONSOLIDATION_SIMILARITY_THRESHOLD", 0.85))
RAW_DIR = pathlib.Path("data/raw")
OUT_DIR = pathlib.Path("data/consolidated")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CONSOLIDATE_PROMPT = """You are a technical documentation editor.
Below are {n} versions of what appears to be the same procedure/topic, with minor differences or improvements over time.
Produce ONE consolidated, clean, complete version that merges all unique improvements.
Keep it factual and concise. Use the most recent and accurate details.
Output only the final document text, no preamble.

--- VERSIONS ---
{versions}
"""


def load_pages() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in RAW_DIR.glob("*.json")]


def group_similar(pages: list[dict]) -> list[list[dict]]:
    texts = [p["text"] for p in pages]
    tfidf = TfidfVectorizer(stop_words="english", max_features=5000).fit_transform(texts)
    sim = cosine_similarity(tfidf)

    visited = set()
    groups = []
    for i in range(len(pages)):
        if i in visited:
            continue
        group = [i]
        visited.add(i)
        for j in range(i + 1, len(pages)):
            if j not in visited and sim[i, j] >= THRESHOLD:
                group.append(j)
                visited.add(j)
        groups.append([pages[k] for k in group])
    return groups


def consolidate_group(group: list[dict]) -> dict:
    if len(group) == 1:
        return group[0]

    versions = "\n\n---\n\n".join(
        f"[{i+1}] {p['notebook']} / {p['section']} / {p['title']}\n{p['text']}"
        for i, p in enumerate(group)
    )
    prompt = CONSOLIDATE_PROMPT.format(n=len(group), versions=versions)
    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    merged_text = response["message"]["content"].strip()

    # Use metadata from the most recently modified page
    base = max(group, key=lambda p: p.get("modified") or "")
    return {
        "id": base["id"],
        "notebook": base["notebook"],
        "section": base["section"],
        "title": base["title"],
        "modified": base["modified"],
        "source_ids": [p["id"] for p in group],
        "text": merged_text,
    }


def consolidate():
    pages = load_pages()
    print(f"Loaded {len(pages)} raw pages")
    groups = group_similar(pages)
    print(f"Grouped into {len(groups)} unique topics (threshold={THRESHOLD})")

    for i, group in enumerate(groups):
        result = consolidate_group(group)
        out_path = OUT_DIR / f"{result['id']}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        label = f"[merged {len(group)}]" if len(group) > 1 else ""
        print(f"  [{i+1}/{len(groups)}] {result['title']} {label}")

    print(f"\nDone. {len(groups)} consolidated pages saved to {OUT_DIR}")


if __name__ == "__main__":
    consolidate()

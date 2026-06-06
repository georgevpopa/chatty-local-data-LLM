# OneNote FAQ RAG Agent

Reads your team's OneNote notebooks via Microsoft Graph API, consolidates duplicate content using a local Ollama LLM, stores everything in ChromaDB, and exposes a simple RAG-powered web UI to query it.

---

## Architecture

```
OneNote (Graph API) → Fetcher → Dedup/Consolidation (Ollama) → ChromaDB → RAG API (FastAPI)
```

---

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running locally
- A model pulled in Ollama, e.g.: `ollama pull mistral`
- Azure AD App Registration (see below)

---

## Azure AD App Registration

You need to register an app in Azure AD to get Graph API access to OneNote.

### Steps

1. Go to [https://portal.azure.com](https://portal.azure.com) and sign in with your work account.

2. Navigate to **Azure Active Directory → App registrations → New registration**.

3. Fill in:
   - **Name**: `OneNote FAQ Agent` (or anything)
   - **Supported account types**: *Accounts in this organizational directory only*
   - **Redirect URI**: `http://localhost:8400` (type: Web)

4. Click **Register**.

5. Note down:
   - **Application (client) ID** → `AZURE_CLIENT_ID` in `.env`
   - **Directory (tenant) ID** → `AZURE_TENANT_ID` in `.env`

6. Go to **Certificates & secrets → New client secret**.
   - Set an expiry, click **Add**.
   - Copy the **Value** immediately → `AZURE_CLIENT_SECRET` in `.env`

7. Go to **API permissions → Add a permission → Microsoft Graph → Delegated permissions**.
   Add these:
   - `Notes.Read`
   - `Notes.Read.All`
   - `User.Read`

8. Click **Grant admin consent** (requires admin rights, or ask your IT admin).

---

## Setup

```bash
git clone <this-repo>
cd onenote-faq-agent
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # fill in your values
```

---

## Usage

### 1. Fetch & index OneNote content

```bash
python -m app.fetcher        # pulls pages from Graph API
python -m app.consolidator   # deduplicates and merges similar content
python -m app.indexer        # stores into ChromaDB
```

Or run all in one:

```bash
python pipeline.py
```

### 2. Start the web UI

```bash
uvicorn app.api:app --reload
```

Open [http://localhost:8000](http://localhost:8000)

---

## Project Structure

```
onenote-faq-agent/
├── app/
│   ├── fetcher.py        # Graph API → raw pages
│   ├── consolidator.py   # Ollama dedup/merge
│   ├── indexer.py        # ChromaDB ingestion
│   ├── rag.py            # RAG query logic
│   ├── api.py            # FastAPI app
│   └── templates/
│       └── index.html    # Web UI
├── data/
│   ├── raw/              # raw fetched pages (JSON)
│   └── consolidated/     # merged/deduped pages (JSON)
├── chroma_db/            # ChromaDB persistent storage
├── pipeline.py           # run full pipeline
├── requirements.txt
└── .env.example
```

---

## Notes

- All LLM calls go through local Ollama — no data leaves your machine.
- ChromaDB is file-based — no separate server needed.
- The `.env` file is gitignored — never commit secrets.

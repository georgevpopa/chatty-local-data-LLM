# 🤖 chatty-local-data-LLM

> A privacy-first AI agent that reads your team's OneNote notebooks, consolidates duplicate content, and lets you query everything through a local RAG-powered chat interface — no data ever leaves your machine.

---

## 💡 The Problem

Our team maintains hundreds (eventually thousands) of pages across shared OneNote notebooks — MOPs, procedures, how-tos, troubleshooting guides. Over time:

- The same procedure gets written 4–5 times with slight variations
- Nobody knows which version is the latest or most accurate
- Finding specific information means manually browsing notebooks
- New team members have no easy way to discover what knowledge exists

---

## 🎯 The Goal

Build a local AI agent that:

1. **Reads** all shared OneNote notebooks automatically via Microsoft Graph API
2. **Consolidates** near-duplicate pages into single, clean, up-to-date documents
3. **Indexes** everything into a local vector database
4. **Answers** natural language questions like:
   - *"What is the MOP to update the SSL certificate on EVNFM?"*
   - *"How do we roll back a failed upgrade on component X?"*
   - *"What are the steps to onboard a new customer to service Y?"*

All processing happens **locally** using Ollama — no cloud LLM, no data sent externally.

---

## 🏗️ Architecture

```
OneNote Notebooks (Microsoft Graph API)
            │
            ▼
    ┌─────────────────┐
    │  fetcher.py     │  → pulls all pages, saves to data/raw/
    └─────────────────┘
            │
            ▼
    ┌─────────────────┐
    │ consolidator.py │  → groups similar pages (TF-IDF cosine similarity)
    │                 │    merges each group into one clean doc (Ollama)
    └─────────────────┘
            │
            ▼
    ┌─────────────────┐
    │   indexer.py    │  → chunks docs, generates embeddings, stores in ChromaDB
    └─────────────────┘
            │
            ▼
    ┌─────────────────┐
    │     rag.py      │  → retrieves top-K relevant chunks for a query
    │     api.py      │    generates answer via Ollama (fully local)
    └─────────────────┘
            │
            ▼
    Simple Web UI (FastAPI + HTML)
    http://localhost:8000
```

**Key technology choices:**
| Component | Tool | Why |
|---|---|---|
| Notebook source | Microsoft Graph API | Live data, no manual export |
| Auth flow | MSAL device code | No passwords stored, works with MFA |
| LLM | Ollama (local) | 100% private, no API costs |
| Vector DB | ChromaDB (local file) | No server needed, persistent |
| Web framework | FastAPI | Lightweight, async |

---

## 📁 Project Structure

```
chatty-local-data-LLM/
├── app/
│   ├── fetcher.py        # Graph API → raw pages (data/raw/)
│   ├── consolidator.py   # Dedup + merge with Ollama
│   ├── indexer.py        # ChromaDB ingestion
│   ├── rag.py            # RAG query logic
│   ├── api.py            # FastAPI endpoints
│   └── templates/
│       └── index.html    # Web UI
├── data/
│   ├── raw/              # fetched pages as JSON (gitignored)
│   └── consolidated/     # merged pages as JSON (gitignored)
├── chroma_db/            # vector store (gitignored)
├── pipeline.py           # runs the full pipeline in one command
├── requirements.txt
└── .env.example          # copy to .env and fill in your values
```

---

## ⚙️ Setup

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- A model pulled: `ollama pull mistral`
- Azure AD App Registration (see below)

### Install

```powershell
git clone https://github.com/georgevpopa/chatty-local-data-LLM.git
cd chatty-local-data-LLM
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # then edit .env with your values
```

---

## 🔑 Azure AD App Registration

You need to register an app in Azure AD to access OneNote via Graph API.

1. Go to [https://portal.azure.com](https://portal.azure.com) → **Azure Active Directory → App registrations → New registration**

2. Fill in:
   - **Name**: `chatty-local-data-LLM`
   - **Supported account types**: *Accounts in this organizational directory only*
   - **Redirect URI**: `http://localhost:8400` (type: Web)

3. After registering, note:
   - **Application (client) ID** → `AZURE_CLIENT_ID`
   - **Directory (tenant) ID** → `AZURE_TENANT_ID`

4. **Certificates & secrets → New client secret** → copy the value → `AZURE_CLIENT_SECRET`

5. **API permissions → Add → Microsoft Graph → Delegated:**
   - `Notes.Read`
   - `Notes.Read.All`
   - `User.Read`

6. Click **Grant admin consent** (or ask your IT admin)

---

## 🚀 Usage

### Run the full pipeline

```powershell
python pipeline.py
```

This will:
1. Open a browser for Microsoft login (device code flow)
2. Fetch all OneNote pages
3. Consolidate duplicates using Ollama
4. Index everything into ChromaDB

### Start the web UI

```powershell
uvicorn app.api:app --reload
```

Open [http://localhost:8000](http://localhost:8000) and start asking questions.

### Run steps individually

```powershell
python -m app.fetcher        # step 1: fetch from OneNote
python -m app.consolidator   # step 2: dedup & merge
python -m app.indexer        # step 3: index into ChromaDB
```

---

## 🗺️ Roadmap

- [x] Graph API fetcher with MSAL device code auth
- [x] TF-IDF based deduplication + Ollama consolidation
- [x] ChromaDB vector store with Ollama embeddings
- [x] RAG query layer
- [x] Basic web UI
- [ ] Scheduled/incremental sync (only fetch changed pages)
- [ ] Notebook filter by name in UI
- [ ] Export consolidated FAQ to a new OneNote section
- [ ] Source highlighting in answers
- [ ] Multi-user support / Teams tab integration

---

## 🔒 Privacy & Security

- **No data leaves your machine** — Ollama runs 100% locally
- **No secrets in git** — `.env`, `data/`, and `chroma_db/` are all gitignored
- **Auth via Microsoft's own MSAL library** — credentials handled by Azure, not stored by this app
- The `.env.example` file contains only placeholder values — fill in your own `.env` locally

---

## 🤝 Contributing

This started as a personal productivity tool for a network/IT ops team. If you're in a similar situation and want to adapt it — PRs welcome.

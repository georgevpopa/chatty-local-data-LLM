"""
Fetches all OneNote pages from Microsoft Graph API and saves raw content to data/raw/.
Uses device code flow (interactive login) — no password stored.
"""
import os
import json
import pathlib
import requests
from msal import PublicClientApplication
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
SCOPES = ["Notes.Read", "Notes.Read.All", "User.Read"]
NOTEBOOK_FILTER = [n.strip() for n in os.getenv("ONENOTE_NOTEBOOK_FILTER", "").split(",") if n.strip()]
RAW_DIR = pathlib.Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

GRAPH = "https://graph.microsoft.com/v1.0"


def get_token() -> str:
    app = PublicClientApplication(CLIENT_ID, authority=f"https://login.microsoftonline.com/{TENANT_ID}")
    # Try silent first (cached)
    accounts = app.get_accounts()
    result = app.acquire_token_silent(SCOPES, account=accounts[0]) if accounts else None
    if not result:
        flow = app.initiate_device_flow(scopes=SCOPES)
        print(flow["message"])  # prints the code + URL for the user
        result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        raise RuntimeError(f"Auth failed: {result.get('error_description')}")
    return result["access_token"]


def graph_get(token: str, url: str) -> dict:
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()


def page_text(token: str, page_id: str) -> str:
    resp = requests.get(
        f"{GRAPH}/me/onenote/pages/{page_id}/content",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser").get_text(separator="\n", strip=True)


def fetch_all():
    token = get_token()
    notebooks = graph_get(token, f"{GRAPH}/me/onenote/notebooks")["value"]

    if NOTEBOOK_FILTER:
        notebooks = [nb for nb in notebooks if nb["displayName"] in NOTEBOOK_FILTER]
        print(f"Filtered to notebooks: {[nb['displayName'] for nb in notebooks]}")

    total = 0
    for nb in notebooks:
        nb_name = nb["displayName"]
        sections_url = f"{GRAPH}/me/onenote/notebooks/{nb['id']}/sections"
        sections = graph_get(token, sections_url)["value"]

        for sec in sections:
            pages_url = f"{GRAPH}/me/onenote/sections/{sec['id']}/pages"
            pages = graph_get(token, pages_url)["value"]

            for page in pages:
                page_id = page["id"]
                out_path = RAW_DIR / f"{page_id}.json"
                if out_path.exists():
                    continue  # skip already fetched

                text = page_text(token, page_id)
                record = {
                    "id": page_id,
                    "notebook": nb_name,
                    "section": sec["displayName"],
                    "title": page["title"],
                    "created": page.get("createdDateTime"),
                    "modified": page.get("lastModifiedDateTime"),
                    "text": text,
                }
                out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                total += 1
                print(f"  [{total}] {nb_name} / {sec['displayName']} / {page['title']}")

    print(f"\nDone. {total} pages saved to {RAW_DIR}")


if __name__ == "__main__":
    fetch_all()

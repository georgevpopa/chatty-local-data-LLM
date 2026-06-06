"""
FastAPI app — serves the web UI and the /query endpoint.
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.rag import query as rag_query

app = FastAPI(title="OneNote FAQ Agent")
templates = Jinja2Templates(directory="app/templates")


class QueryRequest(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/query")
async def query(req: QueryRequest):
    result = rag_query(req.question)
    return result

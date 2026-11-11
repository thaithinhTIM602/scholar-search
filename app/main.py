import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

load_dotenv()

from app.llm import answer_question  # noqa: E402
from app.search import search_papers  # noqa: E402

app = FastAPI(title="Scholar Search")
STATIC = Path(__file__).resolve().parent.parent / "static"


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    from_year: int | None = None
    min_citations: int = 0


@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")


@app.post("/api/ask")
def ask(req: AskRequest):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(500, "ANTHROPIC_API_KEY is not set. See the README.")
    try:
        papers = search_papers(req.question, from_year=req.from_year,
                               min_citations=req.min_citations)
    except Exception as e:
        raise HTTPException(502, f"Paper search failed: {e}")
    try:
        answer, cited = answer_question(req.question, papers)
    except Exception as e:
        raise HTTPException(502, f"AI call failed: {e}")
    return {"answer": answer, "sources": papers, "cited": cited}

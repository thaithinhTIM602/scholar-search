import os
from pathlib import Path

from anthropic import AuthenticationError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# override=True: the .env file wins over any old Codespaces secret with the same name
load_dotenv(override=True)

# Clean up common copy-paste mistakes (spaces, quotes) in the key
_raw_key = os.getenv("ANTHROPIC_API_KEY", "")
_clean_key = _raw_key.strip().strip('"').strip("'").strip()
if _clean_key:
    os.environ["ANTHROPIC_API_KEY"] = _clean_key

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
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or key.startswith("sk-ant-..."):
        raise HTTPException(500, "No API key yet. Open .env, paste your real key from "
                                 "console.anthropic.com, then restart the server.")
    if not key.startswith("sk-ant-"):
        raise HTTPException(500, "That doesn't look like an Anthropic API key (should start "
                                 "with sk-ant-). Check .env, then restart the server.")
    try:
        papers = search_papers(req.question, from_year=req.from_year,
                               min_citations=req.min_citations)
    except Exception as e:
        raise HTTPException(502, f"Paper search failed: {e}")
    try:
        answer, cited = answer_question(req.question, papers)
    except AuthenticationError:
        raise HTTPException(401, "Anthropic rejected the API key. Make a new key at "
                                 "console.anthropic.com, paste it into .env, and restart the server.")
    except Exception as e:
        raise HTTPException(502, f"AI call failed: {e}")
    return {"answer": answer, "sources": papers, "cited": cited}

# Scholar Search

An AI search site that answers questions **only from peer-reviewed journal articles**. No news, no blogs, no random web pages.

**How it works**
1. Your question goes to [OpenAlex](https://openalex.org) (a free index of ~250M scholarly works).
2. Results are filtered to journal articles that aren't retracted and have an abstract. You can also set a minimum year and minimum citation count.
3. Claude gets only those abstracts and is told to answer from them and cite every claim like `[2]`.
4. The code removes any citation number that doesn't match a real retrieved paper, so the model can't invent sources.

## Run it on GitHub (Codespaces, no installs)

1. Create a new **empty** repo on GitHub, then upload these files (drag the folder contents into "uploading an existing file", or push with git).
2. Get an API key at [console.anthropic.com](https://console.anthropic.com).
3. In the repo: **Settings → Secrets and variables → Codespaces → New repository secret**
   Name: `ANTHROPIC_API_KEY`, value: your key.
4. Click **Code → Codespaces → Create codespace on main**. Wait for it to finish installing.
5. In the Codespace terminal:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
6. A popup offers "Open in Browser". Click it and start searching.

Run the tests with `pytest`.

## Run it on your own computer

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then paste your key into .env
uvicorn app.main:app --reload
```
Open http://localhost:8000

## Where to tweak things

| What | File |
|---|---|
| Which papers count as "reputable" (filters) | `app/search.py` → `filters` list |
| How Claude is told to answer | `app/llm.py` → `SYSTEM_PROMPT` |
| Which model | `CLAUDE_MODEL` in `.env` |
| Look of the page | `static/index.html` |

Ideas for next steps: whitelist specific journals (e.g. top econ/finance journals by their OpenAlex source ID), add Semantic Scholar or PubMed as a second source, or pull full open-access PDFs instead of abstracts.

## Limits

- Answers come from **abstracts**, not full papers, so they're summaries of findings, not deep reads.
- "Journal article" isn't a perfect quality filter. Some weak journals get through. A citation minimum or journal whitelist helps.
- Citation counts favor older papers. Leave the minimum at 0 if you want recent work.

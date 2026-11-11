"""Fetch peer-reviewed papers from OpenAlex (free, no key required)."""
import os

import requests

OPENALEX_URL = "https://api.openalex.org/works"
MAX_ABSTRACT_CHARS = 1500


def rebuild_abstract(inverted_index):
    """OpenAlex stores abstracts as {word: [positions]}. Turn that back into text."""
    if not inverted_index:
        return ""
    positions = {}
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))


def _format(work):
    loc = work.get("primary_location") or {}
    source = loc.get("source") or {}
    authors = [
        (a.get("author") or {}).get("display_name", "")
        for a in (work.get("authorships") or [])[:3]
    ]
    if len(work.get("authorships") or []) > 3:
        authors.append("et al.")
    abstract = rebuild_abstract(work.get("abstract_inverted_index"))
    if len(abstract) > MAX_ABSTRACT_CHARS:
        abstract = abstract[:MAX_ABSTRACT_CHARS].rsplit(" ", 1)[0] + "..."
    return {
        "title": work.get("title") or "Untitled",
        "year": work.get("publication_year"),
        "venue": source.get("display_name") or "Unknown journal",
        "authors": ", ".join(a for a in authors if a),
        "citations": work.get("cited_by_count", 0),
        "url": work.get("doi") or loc.get("landing_page_url") or work.get("id"),
        "open_access_url": (work.get("open_access") or {}).get("oa_url"),
        "abstract": abstract,
    }


def search_papers(query, n=8, from_year=None, min_citations=0):
    """Return up to n peer-reviewed, non-retracted journal articles with abstracts."""
    filters = [
        "type:article",
        "is_retracted:false",
        "has_abstract:true",
        "primary_location.source.type:journal",  # journals only, no preprint servers or blogs
    ]
    if from_year:
        filters.append(f"from_publication_date:{int(from_year)}-01-01")
    if min_citations and int(min_citations) > 0:
        filters.append(f"cited_by_count:>{int(min_citations) - 1}")

    params = {
        "search": query,
        "filter": ",".join(filters),
        "per_page": max(n, 10),
        "select": "id,doi,title,publication_year,cited_by_count,primary_location,"
                  "abstract_inverted_index,authorships,open_access",
    }
    # Optional: OpenAlex gives better service to requests that identify themselves.
    if os.getenv("OPENALEX_EMAIL"):
        params["mailto"] = os.getenv("OPENALEX_EMAIL")
    if os.getenv("OPENALEX_API_KEY"):
        params["api_key"] = os.getenv("OPENALEX_API_KEY")

    resp = requests.get(OPENALEX_URL, params=params, timeout=20)
    resp.raise_for_status()
    works = resp.json().get("results", [])
    papers = [_format(w) for w in works]
    return [p for p in papers if p["abstract"]][:n]

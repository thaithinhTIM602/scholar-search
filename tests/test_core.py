from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.llm import clean_citations
from app.main import app
from app.search import rebuild_abstract, search_papers

FAKE_WORK = {
    "id": "https://openalex.org/W1",
    "doi": "https://doi.org/10.1000/xyz",
    "title": "Minimum Wages and Employment",
    "publication_year": 1994,
    "cited_by_count": 3000,
    "primary_location": {"source": {"display_name": "American Economic Review"}},
    "authorships": [{"author": {"display_name": "D. Card"}},
                    {"author": {"display_name": "A. Krueger"}}],
    "open_access": {"oa_url": None},
    "abstract_inverted_index": {"We": [0], "study": [1], "wages": [2]},
}


def test_rebuild_abstract():
    assert rebuild_abstract({"world": [1], "hello": [0]}) == "hello world"
    assert rebuild_abstract(None) == ""


def test_clean_citations_drops_fake_numbers():
    text, used = clean_citations("Claim A [1]. Claim B [7]. Claim C [2][1].", 3)
    assert "[7]" not in text
    assert used == [1, 2]


@patch("app.search.requests.get")
def test_search_formats_and_filters(mock_get):
    mock_get.return_value = MagicMock(json=lambda: {"results": [FAKE_WORK]},
                                      raise_for_status=lambda: None)
    papers = search_papers("minimum wage", from_year=1990, min_citations=50)
    assert papers[0]["venue"] == "American Economic Review"
    assert papers[0]["abstract"] == "We study wages"
    sent_filter = mock_get.call_args.kwargs["params"]["filter"]
    assert "is_retracted:false" in sent_filter
    assert "from_publication_date:1990-01-01" in sent_filter
    assert "cited_by_count:>49" in sent_filter


@patch("app.main.answer_question", return_value=("Answer [1].", [1]))
@patch("app.main.search_papers")
def test_api_endpoint(mock_search, _mock_llm, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    mock_search.return_value = [{"title": "x", "abstract": "y"}]
    r = TestClient(app).post("/api/ask", json={"question": "minimum wage effects"})
    assert r.status_code == 200
    assert r.json()["cited"] == [1]

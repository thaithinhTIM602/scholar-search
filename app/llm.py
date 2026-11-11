"""Ask Claude to answer ONLY from the retrieved papers, then check its citations."""
import os
import re

from anthropic import Anthropic

SYSTEM_PROMPT = """You are a research assistant that answers strictly from the numbered academic sources provided.

Rules:
- Use ONLY the sources given. Do not use outside knowledge, news, or memory.
- Cite every factual claim with the source number in square brackets, like [2] or [1][3].
- If the sources disagree, say so and cite both sides.
- If the sources don't answer the question, say that plainly instead of guessing.
- Keep it to a few short paragraphs. Plain language."""

CITATION_RE = re.compile(r"\[(\d+)\]")


def build_sources_block(papers):
    blocks = []
    for i, p in enumerate(papers, start=1):
        blocks.append(
            f"[{i}] {p['title']} ({p['venue']}, {p['year']}; {p['citations']} citations)\n"
            f"Abstract: {p['abstract']}"
        )
    return "\n\n".join(blocks)


def clean_citations(answer, n_sources):
    """Drop any [n] that doesn't point at a real retrieved paper. Return text + used numbers."""
    used = set()

    def keep_or_drop(match):
        num = int(match.group(1))
        if 1 <= num <= n_sources:
            used.add(num)
            return match.group(0)
        return ""  # model invented a source number, so remove it

    cleaned = CITATION_RE.sub(keep_or_drop, answer)
    return cleaned, sorted(used)


def answer_question(question, papers):
    if not papers:
        return ("I couldn't find peer-reviewed journal articles on that. "
                "Try different keywords or loosen the filters."), []

    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    msg = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5"),
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Sources:\n\n{build_sources_block(papers)}\n\nQuestion: {question}",
        }],
    )
    text = "".join(block.text for block in msg.content if block.type == "text")
    return clean_citations(text, len(papers))

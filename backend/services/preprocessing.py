import re
import unicodedata
from typing import List

from bs4 import BeautifulSoup
from readability import Document

from models.schemas import Card


def extract_plaintext(html: str) -> str:
    """Strip boilerplate/ads from raw HTML and return clean plaintext."""
    # readability-lxml pulls the main article content, discarding nav/ads/footers
    doc = Document(html)
    cleaned_html = doc.summary(html_partial=True)

    # BeautifulSoup strips remaining tags
    soup = BeautifulSoup(cleaned_html, "html.parser")

    # Remove any leftover script/style blocks readability missed
    for tag in soup(["script", "style", "noscript", "iframe", "form"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Normalise unicode (e.g. curly quotes, soft hyphens)
    text = unicodedata.normalize("NFKC", text)

    # Collapse excessive whitespace / blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    return text


def clean_card_summary(summary: str) -> str:
    """Light clean for summaries that arrive as plain text (not full HTML)."""
    # Strip any stray HTML tags
    soup = BeautifulSoup(summary, "html.parser")
    text = soup.get_text(separator=" ")
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def preprocess_cards(raw_cards: List[Card]) -> List[Card]:
    """
    Clean card summaries.
    When Sam's ingestion pipeline passes full HTML bodies in the future,
    call extract_plaintext() on the raw HTML before building the Card.
    For now, sanitise whatever summary text arrives.
    """
    cleaned = []
    for card in raw_cards:
        cleaned_summary = clean_card_summary(card.card_summary)
        cleaned.append(card.copy(update={"card_summary": cleaned_summary}))
    return cleaned

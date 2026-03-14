from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup

GITHUB_TRENDING_URL = "https://github.com/trending"
GITHUB_REPO_URL = "https://github.com/{repo}"
REQUEST_TIMEOUT_SECONDS = 12
MAX_CLEANED_TEXT_CHARS = 1400

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

def _clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _parse_int(text: str) -> int | None:
    match = re.search(r"[\d,]+", text or "")
    if not match:
        return None
    try:
        return int(match.group(0).replace(",", ""))
    except ValueError:
        return None


def _extract_repo_name(article: Any) -> str | None:
    link = article.select_one("h2 a")
    if not link:
        return None
    href = (link.get("href") or "").strip("/")
    if not href:
        return None
    return href


def _extract_repo_description(article: Any) -> str:
    node = article.select_one("p")
    if not node:
        return ""
    return _clean_whitespace(node.get_text(" ", strip=True))


def _extract_language(article: Any) -> str | None:
    node = article.select_one("span[itemprop='programmingLanguage']")
    if not node:
        return None
    value = _clean_whitespace(node.get_text(" ", strip=True))
    return value or None


def _extract_total_stars(article: Any, repo_name: str) -> int | None:
    node = article.select_one(f"a[href='/{repo_name}/stargazers']")
    if not node:
        return None
    return _parse_int(node.get_text(" ", strip=True))


def _extract_today_stars(article: Any) -> int | None:
    candidates = article.select("span.d-inline-block.float-sm-right")
    for candidate in candidates:
        text = _clean_whitespace(candidate.get_text(" ", strip=True)).lower()
        if "stars today" in text:
            return _parse_int(text)
    return None


def _fetch_repo_readme_text(repo_name: str) -> str:
    repo_url = GITHUB_REPO_URL.format(repo=repo_name)
    response = requests.get(
        repo_url,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    readme = soup.select_one("article.markdown-body")
    if not readme:
        return ""
    return _clean_whitespace(readme.get_text(" ", strip=True))


def _split_sentences(text: str) -> list[str]:
    return [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]


def _looks_like_boilerplate(sentence: str) -> bool:
    text = sentence.lower()
    blocked_signals = (
        "installation",
        "install ",
        "quick start",
        "contributing",
        "license",
        "discord",
        "pip install",
        "npm install",
        "docker run",
        "github.com",
        "http://",
        "https://",
    )
    return any(signal in text for signal in blocked_signals)


def _build_cleaned_text(description: str, readme_text: str) -> str:
    combined = _clean_whitespace(f"{description}. {readme_text}")
    if not combined:
        return ""

    kept: list[str] = []
    for sentence in _split_sentences(combined):
        if _looks_like_boilerplate(sentence):
            continue
        kept.append(sentence)
        if len(" ".join(kept)) >= MAX_CLEANED_TEXT_CHARS:
            break

    cleaned = _clean_whitespace(" ".join(kept))
    if not cleaned:
        cleaned = _clean_whitespace(description or combined[:300])

    return cleaned[:MAX_CLEANED_TEXT_CHARS]


def scrape_github_trending(limit: int = 10, include_readme: bool = True) -> list[dict[str, Any]]:
    response = requests.get(
        GITHUB_TRENDING_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("article.Box-row")
    results: list[dict[str, Any]] = []

    for rank, row in enumerate(rows, start=1):
        if len(results) >= limit:
            break

        repo_name = _extract_repo_name(row)
        if not repo_name:
            continue

        description = _extract_repo_description(row)
        language = _extract_language(row)
        total_stars = _extract_total_stars(row, repo_name)
        stars_today = _extract_today_stars(row)

        readme_text = ""
        if include_readme:
            try:
                readme_text = _fetch_repo_readme_text(repo_name)
            except requests.RequestException:
                # Keep the repo row even if README fetch fails.
                readme_text = ""

        source_rank_score = max(0.0, (limit - rank + 1) / max(1, limit))
        cleaned_text = _build_cleaned_text(description, readme_text)

        results.append(
            {
                "schema_version": "1.0.0",
                "id": f"github:{repo_name}",
                "source": "github",
                "source_url": GITHUB_REPO_URL.format(repo=repo_name),
                "title": repo_name,
                "raw_summary": description,
                "raw_content": readme_text or description,
                "pipeline_state": "raw_scraped",
                "preprocessing": {
                    "cleaned_text": cleaned_text,
                    "quality_notes": ["readme_extracted", "keyword_enrichment_pending"],
                    "enrichment_used": False,
                },
                "ranking": {
                    "source_rank_score": source_rank_score,
                    # Backward-compatible alias while the rest of the stack still reads this name.
                    "trending_score": source_rank_score,
                },
                "metadata": {
                    "repo_name": repo_name,
                    "language": language,
                    "stars": total_stars,
                    "stars_today": stars_today,
                    "rank": rank,
                    "freshness_basis": "trending_rank_freshness",
                },
                "provenance": {
                    "collector": "github_trending_scraper",
                    "collector_version": "0.2.0",
                    "dedupe_key": f"github:{repo_name}",
                },
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return results

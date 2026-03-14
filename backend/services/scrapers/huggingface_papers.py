from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

HF_PAPERS_URL = "https://huggingface.co/papers"
HF_PAPER_URL = "https://huggingface.co/papers/{paper_id}"
ARXIV_ABS_URL = "https://arxiv.org/abs/{paper_id}"
ARXIV_PDF_URL = "https://arxiv.org/pdf/{paper_id}.pdf"
REQUEST_TIMEOUT_SECONDS = 15
MAX_CONTENT_CHARS = 2500
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

ARXIV_ID_REGEX = re.compile(r"\b\d{4}\.\d{4,5}(?:v\d+)?\b")


def _clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _truncate(text: str, limit: int) -> str:
    value = _clean_whitespace(text)
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)].rstrip() + "..."


def _extract_paper_ids_from_hf_list(html: str, limit: int) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    paper_ids: list[str] = []
    seen: set[str] = set()
    for link in soup.select("a[href^='/papers/']"):
        href = link.get("href") or ""
        candidate = href.split("/papers/")[-1].strip("/")
        if not candidate:
            continue
        if not ARXIV_ID_REGEX.fullmatch(candidate):
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        paper_ids.append(candidate)
        if len(paper_ids) >= limit:
            break
    return paper_ids


def _extract_hf_detail_fields(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = ""
    title_node = soup.select_one("h1")
    if title_node:
        title = _clean_whitespace(title_node.get_text(" ", strip=True))

    summary = ""
    paragraphs = [p.get_text(" ", strip=True) for p in soup.select("p")]
    cleaned = [_clean_whitespace(p) for p in paragraphs if _clean_whitespace(p)]
    if cleaned:
        summary = max(cleaned, key=len)
    return title, summary


def _extract_arxiv_id_from_text(text: str) -> str | None:
    match = ARXIV_ID_REGEX.search(text or "")
    return match.group(0) if match else None


def _extract_arxiv_id_from_hf_detail(html: str, fallback_id: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.select("a[href]"):
        href = link.get("href") or ""
        if "arxiv.org/abs/" in href or "arxiv.org/pdf/" in href:
            candidate = _extract_arxiv_id_from_text(href)
            if candidate:
                return candidate
    return fallback_id


def _fetch_arxiv_metadata(arxiv_id: str) -> dict[str, Any]:
    url = ARXIV_ABS_URL.format(paper_id=arxiv_id)
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title = ""
    title_meta = soup.select_one("meta[name='citation_title']")
    if title_meta:
        title = _clean_whitespace(title_meta.get("content") or "")

    authors = []
    for node in soup.select("meta[name='citation_author']"):
        content = _clean_whitespace(node.get("content") or "")
        if content:
            authors.append(content)

    abstract = ""
    abstract_meta = soup.select_one("meta[name='citation_abstract']")
    if abstract_meta:
        abstract = _clean_whitespace(abstract_meta.get("content") or "")

    published = ""
    date_meta = soup.select_one("meta[name='citation_date']")
    if date_meta:
        published = _clean_whitespace(date_meta.get("content") or "")

    return {
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "published_date": published,
        "arxiv_abs_url": url,
        "arxiv_pdf_url": ARXIV_PDF_URL.format(paper_id=arxiv_id),
    }


def _download_pdf(arxiv_id: str, pdf_dir: Path) -> Path | None:
    pdf_dir.mkdir(parents=True, exist_ok=True)
    target = pdf_dir / f"{arxiv_id}.pdf"
    if target.exists() and target.stat().st_size > 0:
        return target

    url = ARXIV_PDF_URL.format(paper_id=arxiv_id)
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    if "application/pdf" not in (response.headers.get("Content-Type") or "").lower():
        return None
    target.write_bytes(response.content)
    return target


def scrape_huggingface_papers(
    limit: int = 10,
    download_pdfs: bool = True,
    max_pdf_downloads: int = 5,
    pdf_dir: str | Path = Path("data/scraped/pdfs/huggingface"),
) -> list[dict[str, Any]]:
    response = requests.get(HF_PAPERS_URL, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    paper_ids = _extract_paper_ids_from_hf_list(response.text, limit=limit)
    output: list[dict[str, Any]] = []
    pdf_downloaded = 0

    for rank, paper_id in enumerate(paper_ids, start=1):
        hf_url = HF_PAPER_URL.format(paper_id=paper_id)
        hf_title = ""
        hf_summary = ""
        arxiv_id = paper_id

        try:
            hf_resp = requests.get(hf_url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS)
            hf_resp.raise_for_status()
            hf_html = hf_resp.text
            hf_title, hf_summary = _extract_hf_detail_fields(hf_html)
            arxiv_id = _extract_arxiv_id_from_hf_detail(hf_html, fallback_id=paper_id)
        except requests.RequestException:
            hf_html = ""

        arxiv_meta: dict[str, Any] = {}
        try:
            arxiv_meta = _fetch_arxiv_metadata(arxiv_id)
        except requests.RequestException:
            arxiv_meta = {}

        title = arxiv_meta.get("title") or hf_title or f"Paper {arxiv_id}"
        abstract = arxiv_meta.get("abstract") or hf_summary or ""
        authors = arxiv_meta.get("authors") or []
        published_date = arxiv_meta.get("published_date") or ""

        pdf_path = ""
        if download_pdfs and pdf_downloaded < max_pdf_downloads:
            try:
                maybe_path = _download_pdf(arxiv_id, Path(pdf_dir))
                if maybe_path:
                    pdf_path = str(maybe_path).replace("\\", "/")
                    pdf_downloaded += 1
            except requests.RequestException:
                pdf_path = ""

        cleaned_text = _truncate(abstract or hf_summary or title, MAX_CONTENT_CHARS)
        source_rank_score = max(0.0, (limit - rank + 1) / max(1, limit))

        output.append(
            {
                "schema_version": "1.0.0",
                "id": f"huggingface:{arxiv_id}",
                "source": "huggingface",
                "source_url": hf_url,
                "title": title,
                "raw_summary": abstract or hf_summary,
                "raw_content": _truncate(f"{abstract} {hf_summary}", MAX_CONTENT_CHARS),
                "pipeline_state": "raw_scraped",
                "preprocessing": {
                    "cleaned_text": cleaned_text,
                    "quality_notes": ["paper_metadata_extracted", "keyword_enrichment_pending"],
                    "enrichment_used": False,
                },
                "ranking": {
                    "source_rank_score": source_rank_score,
                    "trending_score": source_rank_score,
                },
                "metadata": {
                    "paper_id": paper_id,
                    "arxiv_id": arxiv_id,
                    "authors": authors,
                    "published_date": published_date,
                    "hf_url": hf_url,
                    "arxiv_abs_url": arxiv_meta.get("arxiv_abs_url"),
                    "arxiv_pdf_url": arxiv_meta.get("arxiv_pdf_url"),
                    "pdf_path": pdf_path,
                    "pdf_downloaded": bool(pdf_path),
                    "rank": rank,
                    "freshness_basis": "huggingface_papers_rank_freshness",
                },
                "provenance": {
                    "collector": "huggingface_papers_scraper",
                    "collector_version": "0.1.0",
                    "dedupe_key": f"huggingface:{arxiv_id}",
                },
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return output

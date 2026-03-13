"""
GitHub Repo Preprocessor - Fetches and extracts text from GitHub repositories.
Uses the GitHub API to pull repo metadata, README, and directory structure,
then produces a consolidated text file for downstream concept extraction.
"""

import os
import re
import json
import base64
import logging
from pathlib import Path
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


def parse_github_url(url: str) -> tuple[str, str]:
    """
    Extract owner and repo name from a GitHub URL.

    Args:
        url: GitHub repository URL (e.g., https://github.com/microsoft/BitNet)

    Returns:
        Tuple of (owner, repo_name)
    """
    url = url.strip().rstrip("/")
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {url}")
    return parts[0], parts[1]


def _get_headers(token: str | None = None) -> dict:
    """Build request headers, optionally with auth token."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def fetch_repo_metadata(owner: str, repo: str, token: str | None = None) -> dict:
    """Fetch core repository metadata from GitHub API."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    resp = requests.get(url, headers=_get_headers(token), timeout=30)
    resp.raise_for_status()
    data = resp.json()

    return {
        "full_name": data.get("full_name", ""),
        "description": data.get("description", ""),
        "language": data.get("language", ""),
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "topics": data.get("topics", []),
        "license": (data.get("license") or {}).get("name", "Unknown"),
        "created_at": data.get("created_at", ""),
        "updated_at": data.get("updated_at", ""),
        "homepage": data.get("homepage", ""),
        "default_branch": data.get("default_branch", "main"),
    }


def fetch_readme(owner: str, repo: str, token: str | None = None) -> str:
    """Fetch and decode the repository README file."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme"
    resp = requests.get(url, headers=_get_headers(token), timeout=30)

    if resp.status_code == 404:
        logger.warning(f"No README found for {owner}/{repo}")
        return ""

    resp.raise_for_status()
    data = resp.json()

    content_b64 = data.get("content", "")
    if not content_b64:
        return ""

    try:
        return base64.b64decode(content_b64).decode("utf-8", errors="replace")
    except Exception as e:
        logger.error(f"Failed to decode README for {owner}/{repo}: {e}")
        return ""


def fetch_directory_tree(
    owner: str, repo: str, branch: str = "main", token: str | None = None
) -> list[str]:
    """Fetch the top-level directory tree of the repository."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}"
    resp = requests.get(
        url, headers=_get_headers(token), params={"recursive": "false"}, timeout=30
    )

    if resp.status_code != 200:
        logger.warning(f"Could not fetch tree for {owner}/{repo}: {resp.status_code}")
        return []

    data = resp.json()
    tree = data.get("tree", [])

    entries = []
    for item in tree:
        item_type = "dir" if item["type"] == "tree" else "file"
        entries.append(f"[{item_type}] {item['path']}")

    return entries


def clean_readme_markdown(readme_text: str) -> str:
    """Strip markdown formatting to produce clean readable text."""
    text = readme_text

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove image references ![alt](url)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)

    # Convert links [text](url) to just text
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)

    # Remove badge-style images and shields.io references
    text = re.sub(r"\[!\[.*?\]\(.*?\)\]\(.*?\)", "", text)

    # Remove markdown emphasis markers but keep text
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    # Remove code block markers (keep content)
    text = re.sub(r"```[\w]*\n?", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Clean up heading markers
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def build_repo_text(
    repo_url: str, metadata: dict, readme_raw: str, tree: list[str]
) -> str:
    """Assemble all fetched data into a single structured text document."""

    sections = []

    # Header / metadata
    sections.append(f"SOURCE_TYPE: github_repo")
    sections.append(f"SOURCE_URL: {repo_url}")
    sections.append(f"REPO: {metadata['full_name']}")
    sections.append(f"DESCRIPTION: {metadata['description']}")
    sections.append(f"LANGUAGE: {metadata['language']}")
    sections.append(f"STARS: {metadata['stars']}")
    sections.append(f"FORKS: {metadata['forks']}")
    sections.append(f"TOPICS: {', '.join(metadata['topics'])}")
    sections.append(f"LICENSE: {metadata['license']}")
    sections.append(f"CREATED: {metadata['created_at']}")
    sections.append(f"UPDATED: {metadata['updated_at']}")
    sections.append("---\n")

    # README
    if readme_raw:
        cleaned_readme = clean_readme_markdown(readme_raw)
        sections.append("README CONTENT:")
        sections.append(cleaned_readme)
        sections.append("")

    # Directory structure
    if tree:
        sections.append("REPOSITORY STRUCTURE:")
        for entry in tree:
            sections.append(f"  {entry}")
        sections.append("")

    return "\n".join(sections)


def process_github_link(link_file_path: str, output_path: str, token: str | None = None) -> str:
    """
    Full pipeline: read GitHub URL from file, fetch data, and save processed text.

    Args:
        link_file_path: Path to a .txt file containing a GitHub repo URL.
        output_path: Path to write the processed text output.
        token: Optional GitHub personal access token for higher rate limits.

    Returns:
        The assembled text content.
    """
    with open(link_file_path, "r", encoding="utf-8") as f:
        repo_url = f.read().strip()

    if not repo_url:
        logger.error(f"Empty URL in {link_file_path}")
        return ""

    logger.info(f"Processing GitHub repo: {repo_url}")

    owner, repo = parse_github_url(repo_url)

    metadata = fetch_repo_metadata(owner, repo, token)
    readme_raw = fetch_readme(owner, repo, token)
    tree = fetch_directory_tree(owner, repo, metadata.get("default_branch", "main"), token)

    output_content = build_repo_text(repo_url, metadata, readme_raw, tree)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_content)

    logger.info(
        f"Saved processed repo text to {output_path} "
        f"({len(output_content)} chars)"
    )
    return output_content

"""Image generation for cards using Google Imagen 3, with Pexels fallback."""

import base64
import os
import time
import uuid
import requests
from google import genai
from config import get_settings

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"

_used_ids: set[int] = set()

# Directory to save generated images
_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "images")
os.makedirs(_IMAGES_DIR, exist_ok=True)


def reset_used_ids():
    """Call at start of pipeline run to reset duplicate tracking."""
    _used_ids.clear()


def _build_prompt(title: str, keywords: list[str], thumbnail_keyword: str, orientation: str = "vertical") -> str:
    """Build a prompt with a cohesive color tone but content-specific subject."""
    kw_str = ", ".join(keywords[:3]) if keywords else "technology"
    orient_word = "vertical portrait" if orientation == "vertical" else "horizontal landscape"
    return (
        f"A cinematic {orient_word} editorial photograph. "
        f"Subject: a creative, detailed scene that directly illustrates the topic \"{title[:80]}\". "
        f"Related themes: {kw_str}. "
        f"Be creative and specific with the subject matter — show relevant objects, "
        f"environments, or symbolic scenes that tell a story about this topic. "
        f"For example: a robot hand for AI agents, a glowing shield for security, "
        f"a branching tree for open-source, a fast car for speed optimization, etc. "
        f"STRICT RULES: "
        f"1. Any text in the image MUST be in English using Latin alphabet ONLY. "
        f"2. Absolutely NO Chinese, Japanese, Korean, Arabic, Cyrillic, or any non-Latin script. "
        f"3. Keep text minimal — prefer no text at all unless it naturally fits. "
        f"4. No random characters, no gibberish, no garbled text. "
        f"Consistent color grading: dark moody background in deep navy and charcoal, "
        f"accent lighting in teal and warm amber, cinematic rim lighting, shallow depth of field. "
        f"Premium quality, editorial magazine photography. "
        f"No logos, no watermarks, no UI screenshots."
    )


def generate_image_google(prompt: str, aspect_ratio: str = "9:16") -> str:
    """Generate an image using Google Imagen 4. Saves to disk, returns local URL."""
    settings = get_settings()
    if not settings.google_api_key:
        return ""

    try:
        client = genai.Client(api_key=settings.google_api_key)
        response = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=genai.types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
            ),
        )

        if not response.generated_images:
            print("  [WARN] Imagen returned no images")
            return ""

        # Save image to disk so it persists (unlike DALL-E temp URLs)
        image_data = response.generated_images[0].image.image_bytes
        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(_IMAGES_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(image_data)

        # Return URL that the FastAPI static files will serve
        return f"/static/images/{filename}"

    except Exception as exc:
        print(f"  [WARN] Google Imagen generation failed: {exc}")
        return ""


def _search_pexels(query: str, width: int = 800, height: int = 600) -> str:
    """Fallback: search Pexels for a relevant image."""
    settings = get_settings()
    if not settings.pexels_api_key:
        return ""

    try:
        resp = requests.get(
            PEXELS_SEARCH_URL,
            headers={"Authorization": settings.pexels_api_key},
            params={"query": query, "per_page": 15, "orientation": "landscape"},
            timeout=10,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        if not photos:
            return ""

        for photo in photos:
            pid = photo.get("id")
            if pid not in _used_ids:
                _used_ids.add(pid)
                original = photo.get("src", {}).get("original", "")
                if original:
                    return f"{original}?auto=compress&cs=tinysrgb&w={width}&h={height}&fit=crop"
        return ""
    except Exception:
        return ""


def get_card_image(keywords: list[str], title: str = "", thumbnail_keyword: str = "",
                    max_retries: int = 3, orientation: str = "vertical") -> str:
    """Generate an image for a card or briefing.

    orientation: "vertical" (9:16) for swipe cards, "landscape" (16:9) for briefing blocks.
    """
    aspect = "9:16" if orientation == "vertical" else "16:9"
    print(f"  Generating {orientation} image for: {title[:50]}...")

    for attempt in range(1, max_retries + 1):
        prompt = _build_prompt(title, keywords, thumbnail_keyword, orientation=orientation)
        url = generate_image_google(prompt, aspect_ratio=aspect)
        if url:
            return url
        if attempt < max_retries:
            wait = attempt * 5
            print(f"  Retrying image generation (attempt {attempt + 1}/{max_retries}) after {wait}s...")
            time.sleep(wait)

    # Fallback to Pexels
    print(f"  Falling back to Pexels for: {title[:50]}")
    query = f"{thumbnail_keyword or ''} {' '.join(keywords[:2])} abstract technology"
    return _search_pexels(query)

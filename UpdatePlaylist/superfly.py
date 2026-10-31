import time
import logging
from typing import List

import requests
from bs4 import BeautifulSoup

SUPERFLY_URL = "https://superfly.fm/shows/superfly-yachthafen"


def parse_superfly_html(html: bytes) -> List[str]:
    """Parse Superfly Yachthafen HTML and return ["artist - title", ...] in lowercase.

    The playlist is a grid of card <div>s following the "Playlist – Show vom" heading,
    each holding a <p>Title</p> followed by a <p>– Artist</p>.
    """
    soup = BeautifulSoup(html, "html.parser")

    results: List[str] = []

    heading = next(
        (
            h for h in soup.find_all(["h1", "h2", "h3", "h4"])
            if "playlist" in h.get_text().lower() and "show vom" in h.get_text().lower()
        ),
        None,
    )
    if heading is None:
        logging.warning("Superfly parse: playlist heading not found")
        return results

    grid = heading.find_next_sibling("div")
    if grid is None:
        logging.warning("Superfly parse: playlist grid not found after heading")
        return results

    for card in grid.find_all("div", recursive=False):
        paragraphs = [p.get_text(" ", strip=True) for p in card.find_all("p")]
        paragraphs = [p for p in paragraphs if p]
        if len(paragraphs) < 2 or not paragraphs[1].startswith(("–", "—", "-")):
            continue
        title = _normalize_punct(paragraphs[0])
        artist = _normalize_punct(paragraphs[1].lstrip("–—-").strip())

        pair = f"{_first_artist(artist)} - {title}".strip().lower()
        if _looks_like_pair(pair):
            results.append(pair)

    return results


def get_superfly_playlist() -> List[str]:
    """Fetch the Superfly page and parse it into ["artist - title", ...]."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; YachthafenPlaylistBot/1.0; +https://github.com/AndreasScheicher/yachthafen-playlist)",
        "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
    }

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        resp = requests.get(SUPERFLY_URL, headers=headers, timeout=15)
        # Retry on throttle/server errors
        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(0.5 * attempt)
            continue
        resp.raise_for_status()
        tracks = parse_superfly_html(resp.content)
        if tracks:
            logging.info("accessed superfly playlist, %d tracks found", len(tracks))
        else:
            logging.warning("superfly playlist parsed but empty — site structure may have changed")
        return tracks

    # If we fell out of the loop without successful return, raise
    resp.raise_for_status()
    return []


def _normalize_punct(s: str) -> str:
    return (
        s.replace("–", "-")
        .replace("—", "-")
        .replace("`", "'")
        .strip()
    )


def _first_artist(artist: str) -> str:
    # Multiple artists are listed as "A; B; C". Spotify matching compares
    # against one artist at a time, so keep only the primary one.
    return artist.split(";", 1)[0].strip()


def _looks_like_pair(s: str) -> bool:
    if "-" not in s:
        return False
    left, right = [p.strip() for p in s.split("-", 1)]
    return len(left) >= 2 and len(right) >= 2

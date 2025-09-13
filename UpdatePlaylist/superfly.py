import time
import logging
from typing import List

import requests
from bs4 import BeautifulSoup

SUPERFLY_URL = "https://superfly.fm/shows/superfly-yachthafen"


def parse_superfly_html(html: bytes) -> List[str]:
    """Parse Superfly Yachthafen HTML and return ["artist - title", ...] in lowercase.

    Supports two patterns observed on the site:
    1) Card layout: elements with classes .team-member containing .song-title and .artist
    2) Text lines: alternating lines of "Title" then "– Artist"
    """
    soup = BeautifulSoup(html, "html.parser")

    results: List[str] = []

    # 1) Structured cards first
    members = soup.select(".team-member")
    for card in members:
        title_el = card.select_one(".song-title")
        # Artist can be in .artist or inside a <strong> within a .meta block prefixed by '- '
        artist_el = (
            card.select_one(".artist")
            or card.select_one(".meta strong")
            or card.select_one("strong")
        )
        if not title_el or not artist_el:
            # As a fallback, try to derive from .meta text if present
            meta_el = card.select_one(".meta")
            if not title_el or not meta_el:
                continue
            title = _normalize_punct(title_el.get_text(" ", strip=True))
            meta_text = meta_el.get_text(" ", strip=True)
            # Strip leading dash/en-dash and whitespace
            artist = _normalize_punct(meta_text.lstrip("–—-").strip())
        else:
            title = _normalize_punct(title_el.get_text(" ", strip=True))
            artist_raw = artist_el.get_text(" ", strip=True)
            artist = _normalize_punct(artist_raw.lstrip("–—-").strip())

        pair = f"{artist} - {title}".strip().lower()
        if _looks_like_pair(pair):
            results.append(pair)

    if results:
        return results

    # 2) Fallback to text-line pairing
    lines = [s.strip() for s in soup.stripped_strings if s and s.strip()]

    # Find the anchor heading for the playlist section
    anchor_idx = None
    for i, line in enumerate(lines):
        low = line.lower()
        if "playlist" in low and "show vom" in low:
            anchor_idx = i
            break

    if anchor_idx is None:
        logging.warning("Superfly parse: playlist anchor not found")
        start = 0
    else:
        start = anchor_idx + 1

    def _strip_quotes(s: str) -> str:
        s = s.strip()
        # Normalize curly quotes and ASCII quotes
        quotes = ('"', "'", "“", "”", "„", "‚", "’", "`")
        while len(s) >= 2 and (s[0] in quotes and s[-1] in quotes):
            s = s[1:-1].strip()
        return s

    i = start
    while i < len(lines) - 1:
        title_line = lines[i]
        artist_line = lines[i + 1]

        # Accept patterns like "Title" and – Artist / - Artist
        is_title = title_line.startswith(("\"", "“", "„")) or title_line.endswith(("\"", "”"))
        is_artist = artist_line.startswith("–") or artist_line.startswith("-")

        if is_title and is_artist:
            title = _strip_quotes(title_line)
            artist = artist_line.lstrip("–-").strip()

            # Normalize punctuation and whitespace
            title = _normalize_punct(title)
            artist = _normalize_punct(artist)

            pair = f"{artist} - {title}".strip().lower()
            if _looks_like_pair(pair):
                results.append(pair)
            i += 2
        else:
            i += 1

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


def _looks_like_pair(s: str) -> bool:
    if "-" not in s:
        return False
    left, right = [p.strip() for p in s.split("-", 1)]
    return len(left) >= 2 and len(right) >= 2

"""Filter TV torrent titles by show year and show-name position before SxxExx."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from rapidfuzz import fuzz

_YEAR_CANDIDATE_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
_SEPARATOR_RE = re.compile(r"[._\-]+")
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'s)?", re.IGNORECASE)

# Scene releases usually cite TV years in this window.
_MIN_TV_YEAR = 1950
_STOPWORDS = frozenset({"the", "a", "an", "of", "and", "in", "to"})


def _max_plausible_tv_year() -> int:
    return datetime.now(timezone.utc).year + 1


def extract_tv_years_from_title(title: str) -> list[int]:
    """
    Pull plausible TV/air years from a release title.

    Ignores resolution tokens (1080p, 2160p) and WxH dimensions (1920x1080)
    that also look like four-digit numbers.
    """
    years: list[int] = []
    for match in _YEAR_CANDIDATE_RE.finditer(title):
        year = int(match.group(1))
        start, end = match.start(), match.end()

        if not (_MIN_TV_YEAR <= year <= _max_plausible_tv_year()):
            continue

        # 2160p / 1080p-style resolution (1080 is not matched by 19xx|20xx).
        if end < len(title) and title[end].lower() in "pi":
            continue

        # 1920x1080 / 3840x2160 dimensions.
        if end < len(title) and title[end].lower() == "x":
            continue
        if start > 0 and title[start - 1].lower() == "x":
            continue

        years.append(year)
    return years


def torrent_title_conflicts_with_show_year(title: str, show_year: int | None) -> bool:
    """
    Return True when a release title cites a year that is not the watchlist show year.

    Titles with no plausible TV year are kept (ambiguous — typical for classic releases).
    When one or more TV years appear, at least one must equal ``show_year``.
    """
    if show_year is None:
        return False
    years = extract_tv_years_from_title(title)
    if not years:
        return False
    return show_year not in years


def normalize_title_for_match(text: str) -> str:
    """Lowercase release title with scene separators collapsed to spaces."""
    cleaned = _SEPARATOR_RE.sub(" ", text or "")
    return re.sub(r"\s+", " ", cleaned).strip().lower()


def _strip_leading_article(text: str) -> str:
    for article in ("the ", "a ", "an "):
        if text.startswith(article):
            return text[len(article) :]
    return text


def _normalize_token(token: str) -> str:
    cleaned = token.lower().strip("'\"")
    if cleaned.endswith("'s"):
        return cleaned[:-2]
    return cleaned


def _significant_show_tokens(show_title: str) -> list[str]:
    norm = normalize_title_for_match(show_title)
    tokens: list[str] = []
    seen: set[str] = set()
    for match in _TOKEN_RE.finditer(norm):
        token = _normalize_token(match.group(0))
        if not token or token in _STOPWORDS or token in seen:
            continue
        seen.add(token)
        tokens.append(token)
    return tokens


def _token_present_in_text(token: str, text: str) -> bool:
    if not token:
        return True
    for match in _TOKEN_RE.finditer(text):
        candidate = _normalize_token(match.group(0))
        if candidate == token:
            return True
        if token.endswith("s") and candidate == token[:-1]:
            return True
        if candidate.endswith("s") and token == candidate[:-1]:
            return True
    return False


def _show_tokens_present_before_episode(prefix: str, show_title: str) -> bool:
    """Every significant show-title word must appear before SxxExx."""
    show_tokens = _significant_show_tokens(show_title)
    if not show_tokens:
        return True
    prefix_norm = normalize_title_for_match(prefix)
    return all(_token_present_in_text(token, prefix_norm) for token in show_tokens)


def _episode_marker_pattern(season: int, episode: int) -> re.Pattern[str]:
    return re.compile(rf"[Ss]{season:02d}[Ee]{episode:02d}", re.IGNORECASE)


def _show_prefix_match_score(prefix: str, show_title: str) -> float:
    if not prefix or not show_title:
        return 0.0
    prefix_norm = normalize_title_for_match(prefix)
    show_norm = normalize_title_for_match(show_title)
    if not prefix_norm or not show_norm:
        return 0.0
    score = float(fuzz.partial_ratio(show_norm, prefix_norm))
    alt = float(
        fuzz.partial_ratio(
            _strip_leading_article(show_norm),
            _strip_leading_article(prefix_norm),
        )
    )
    return max(score, alt)


def torrent_title_conflicts_with_show_before_episode(
    title: str,
    show_title: str,
    season: int,
    episode: int,
    *,
    min_prefix_match_score: float = 80.0,
) -> bool:
    """
    Reject when the watchlist show is not in the title *before* SxxExx.

    Scene releases should read like ``Show Title [Year] S01E02 ...-Group``.
    A torrent named ``Ms Marvel S01E02 ...-thePunisher`` is rejected for
    ``The Punisher S01E02`` because only the release group cites the target show.
    """
    if not show_title or not str(show_title).strip():
        return False

    match = _episode_marker_pattern(season, episode).search(title)
    if not match:
        return True

    prefix = title[: match.start()]
    suffix = title[match.end() :]

    if _show_tokens_present_before_episode(prefix, show_title):
        return False

    suffix_score = _show_prefix_match_score(suffix, show_title)
    if suffix_score >= min_prefix_match_score:
        return True

    prefix_score = _show_prefix_match_score(prefix, show_title)
    if prefix_score >= min_prefix_match_score:
        return True

    return True

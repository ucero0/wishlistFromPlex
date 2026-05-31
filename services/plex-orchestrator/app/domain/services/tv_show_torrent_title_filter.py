"""Filter TV torrent titles whose embedded year does not match the watchlist show."""
from __future__ import annotations

import re
from datetime import datetime, timezone

_YEAR_CANDIDATE_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")

# Scene releases usually cite TV years in this window.
_MIN_TV_YEAR = 1950


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

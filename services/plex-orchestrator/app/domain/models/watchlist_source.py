from enum import Enum


class WatchlistSource(str, Enum):
    PLEX = "plex"
    TMDB = "tmdb"

"""Season/episode reference for TV automation."""
from pydantic import BaseModel, ConfigDict


class TvEpisode(BaseModel):
    model_config = ConfigDict(frozen=True)

    season: int
    episode: int
    name: str | None = None

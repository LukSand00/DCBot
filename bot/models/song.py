from dataclasses import dataclass
from enum import Enum

class SourceType(Enum):
    LOCAL = 'local'
    YOUTUBE = 'youtube'

@dataclass
class Song:
    song_name: str
    source: SourceType = SourceType.LOCAL
    full_path: str | None = None
    yt_url: str | None = None
    duration: int | None = None
    artist: str | None = None
    parent_catalog: str | None = None

    def __post_init__(self):
        self.source = SourceType(self.source)

    def format_duration(self):
        if self.duration is None:
            return 'Unknown length.'
        else:
            minutes, seconds = divmod(self.duration, 60)
            return f'Duration: {minutes}:{seconds}.'

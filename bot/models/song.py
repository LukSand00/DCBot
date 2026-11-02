from dataclasses import dataclass

@dataclass
class Song:
    song_name: str
    full_path: str
    duration: int | None = None
    artist: str | None = None
    parent_catalog: str | None = None

    def format_duration(self):
        if self.duration is None:
            return 'Unknown length.'
        else:
            minutes, seconds = divmod(self.duration, 60)
            return f'Duration: {minutes}:{seconds}.'

import os
import asyncio
from urllib.parse import urlparse

from pathlib import Path
from models.song import Song, SourceType

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, match_filter_func


DOWNLOAD_DIR = Path(os.environ['DOWNLOAD_DIR'])

class DownloadFailed(Exception):
    pass

class DownloaderService:

    MAX_RESULTS = 5
    MAX_DURATION_SECONDS = 600

    def __init__(self):
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.opts: dict = {
            "format": "bestaudio/best",
            "outtmpl": str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
            "extract_flat": "in_playlist",
            "noplaylist": True,
            "quiet": True,
            'match_filter': match_filter_func(
                'duration <= 600'
            ),
        }

    async def search_video(self, query: str) -> list[Song]:
        try:
            with YoutubeDL(self.opts) as ydl:
                result = ydl.extract_info(f"ytsearch{self.MAX_RESULTS}:{query}", download=False)
                if len(result["entries"]) > 0:
                    return [self._song_from_ytdlp(r) for r in result["entries"]]
                else:
                    raise ValueError("No results found.")
        except DownloadError as e:
            raise DownloadFailed(str(e)) from e

    def _song_from_ytdlp(self, result: dict) -> Song:
        return Song(
            source=SourceType.YOUTUBE,
            song_name=result["title"],
            duration=result["duration"],
            yt_url=result["url"],
            artist=result["channel"]
        )

    def _download_sync(self, url: str, song: Song = None) -> Song:
        try:
            with YoutubeDL(self.opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info.get("_type") == "playlist" or "entries" in info:
                    raise DownloadFailed("Playlists are not allowed.")
                if info.get("duration") > self.MAX_DURATION_SECONDS:
                    raise DownloadFailed(f"Video is too long.")
                path = Path(ydl.prepare_filename(info))
                ydl.download([url])
                if song:
                    song.full_path = path
                    return song
                return Song(song_name=info["title"], full_path=path, duration=info.get("duration"), source=SourceType.YOUTUBE)
        except DownloadError as e:
            raise DownloadFailed(str(e)) from e

    def clear_directory(self):
        for file in DOWNLOAD_DIR.iterdir():
            if file.is_file():
                file.unlink()

    def delete_temp(self, path):
        path = Path(path)
        path.unlink()

    async def download(self, url: str, song: Song = None) -> Song:
        return await asyncio.to_thread(self._download_sync, url, song)
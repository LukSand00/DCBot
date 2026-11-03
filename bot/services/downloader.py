import os
import asyncio
import shutil
from pathlib import Path
from models.song import Song

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


DOWNLOAD_DIR = Path(os.environ['DOWNLOAD_DIR'])

class DownloadFailed(Exception):
    pass

class Downloader:
    def __init__(self):
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.opts = {
            "format": "bestaudio/best",
            "outtmpl": str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
            "extract_flat": "in_playlist",
            "noplaylist": True,
            "quiet": True,
        }

    def _download_sync(self, url: str) -> Song:
        try:
            with YoutubeDL(self.opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info.get("_type") == "playlist" or "entries" in info:
                    raise DownloadFailed("Playlists are not allowed.")
                path = Path(ydl.prepare_filename(info))
                return Song(song_name=info["title"], full_path=path, duration=info.get("duration"))
        except DownloadError as e:
            raise DownloadFailed(str(e)) from e

    def clear_directory(self):
        for file in DOWNLOAD_DIR.iterdir():
            if file.is_file():
                file.unlink()


    async def download(self, url: str) -> Song:
        return await asyncio.to_thread(self._download_sync, url)
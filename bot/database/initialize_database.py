import os
import sqlite3
from dataclasses import dataclass
from contextlib import closing
from pathlib import Path

import mutagen
from dotenv import load_dotenv

load_dotenv()

ALLOWED_EXTENSIONS = {'.mp3', '.wav'}
SOURCE_PATH = str(os.getenv("SOURCE_PATH"))
DATABASE_PATH = str(os.getenv("DATABASE_PATH"))

@dataclass()
class Track:
    song_name: str
    full_path: str
    parent_catalog: str
    duration: int | None = None
    artist: str | None = None

def create_tables(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS songs(song_name TEXT PRIMARY KEY UNIQUE, artist TEXT, full_path TEXT NOT NULL, duration INTEGER, parent_catalog TEXT NOT NULL)")

def read_track(path: Path) -> Track | None:
    try:
        audio = mutagen.File(path)
    except mutagen.MutagenError:
        return None
    if audio is None or audio.info is None:
        return None

    artists = audio.get("artist")
    return Track(
        song_name=path.name,
        full_path=str(path.resolve()),
        parent_catalog=path.parent.name,
        duration=int(audio.info.length),
        artist=artists[0] if artists else None,
    )

def scan_libraries(source: Path) -> list[str]:
    tracks = []
    for path in source.rglob('*'):
        if path.is_file() and path.suffix in ALLOWED_EXTENSIONS:
            if track := read_track(path):
                tracks.append(track)
    return tracks

def insert_data(conn: sqlite3.Connection, tracks: list[Track]) -> None:
    conn.executemany("""
         INSERT OR IGNORE INTO songs (song_name,full_path,parent_catalog,duration,artist) 
         VALUES (:song_name,:full_path,:parent_catalog,:duration,:artist)""",
                [vars(t) for t in tracks],)
    conn.commit()

def main() -> None:
    source = Path(SOURCE_PATH)
    db_path = Path(DATABASE_PATH)

    track_list = scan_libraries(source)
    with closing(sqlite3.connect(db_path)) as conn:
        create_tables(conn)
        insert_data(conn, track_list)


if __name__ == '__main__':
    main()

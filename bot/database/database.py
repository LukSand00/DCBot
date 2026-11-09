import os
from pathlib import Path

import aiosqlite
import mutagen
from models.song import Song

class Database:
    # CONSTANT USED AS ESCAPE CHARACTER IN SQL QUERIES
    ESCAPE_CHARACTER = '|'
    # LIST OF CHARACTERS THAT NEED TO BE ESCAPED IN VALUES USED FOR QUERIES
    # DO NOT PUT ESCAPE_CHARACTER HERE
    CHARS_TO_ESCAPE = ('%','_')
    ALLOWED_EXTENSIONS = {'.mp3', '.wav'}
    SOURCE_PATH = str(os.getenv("SOURCE_PATH"))
    DATABASE_PATH = str(os.getenv("DATABASE_PATH"))

    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None

    async def connect(self):
        if self.connection is not None:
            raise RuntimeError('Database already connected.')
        if not os.path.exists(self.db_path):
            print('Database does not exist. Initializing database...')
            return await self.initialize_database()
        connection = await aiosqlite.connect(self.db_path)
        try:
            connection.row_factory = aiosqlite.Row
            await connection.execute('PRAGMA foreign_keys = ON')
            await connection.execute('PRAGMA journal_mode = WAL')
        except BaseException:
            await connection.close()
            raise
        self.connection = connection


    async def close(self):
        if self.connection is not None:
            await self.connection.close()
            self.connection = None

    async def fetch_songs(self, song_name: str):
        if self.connection is None:
            raise RuntimeError('Database is not connected.')
        adjusted_name = f"%{Database.escape_characters(song_name)}%"
        async with self.connection.execute("""
                                           SELECT song_name, full_path, duration FROM songs
                                           WHERE song_name LIKE ? ESCAPE ? 
                                           ORDER BY song_name LIMIT 11""", (adjusted_name,Database.ESCAPE_CHARACTER,),) as cursor:
            rows = await cursor.fetchall()
        return [Song(**row) for row in rows]

    async def reload_songs(self):
        if self.connection is None:
            raise RuntimeError('Database is not connected.')
        init = DatabaseManaging(self)
        songs = await init.scan_libraries()
        await init.insert_data(songs)

    async def initialize_database(self):
        if self.connection is None:
            self.connection = await aiosqlite.connect(self.db_path)
        init = DatabaseManaging(self)
        await init.create_tables()
        songs = await init.scan_libraries()
        await init.insert_data(songs)

    @classmethod
    def escape_characters(cls,song_name: str):
        escape_char = cls.ESCAPE_CHARACTER
        escaped_name = song_name.replace(escape_char, escape_char + escape_char)
        for char in cls.CHARS_TO_ESCAPE:
            escaped_name = escaped_name.replace(char,escape_char + char)
        return escaped_name

class DatabaseManaging:
    ALLOWED_EXTENSIONS = {'.mp3', '.wav'}
    SOURCE_PATH = Path(os.environ.get("SOURCE_PATH"))
    DATABASE_PATH = Path(os.environ.get("DATABASE_PATH"))

    def __init__(self, database: Database):
        self.database = database

    async def create_tables(self) -> None:
        await self.database.connection.execute("CREATE TABLE IF NOT EXISTS songs(song_name TEXT PRIMARY KEY UNIQUE, artist TEXT, full_path TEXT NOT NULL, duration INTEGER, parent_catalog TEXT NOT NULL)")

    async def read_track(self, path: Path) -> Song | None:
        try:
            audio = mutagen.File(self.SOURCE_PATH / path)
        except mutagen.MutagenError:
            return None
        if audio is None or audio.info is None:
            return None

        artists = audio.get("artist")
        return Song(
            song_name=path.name,
            full_path=str(path.resolve()),
            parent_catalog=path.parent.name,
            duration=int(audio.info.length),
            artist=artists[0] if artists else None,
        )

    async def scan_libraries(self) -> list[str]:
        tracks = []
        for path in self.SOURCE_PATH.rglob('*'):
            if path.is_file() and path.suffix in self.ALLOWED_EXTENSIONS:
                if track := await self.read_track(path):
                    tracks.append(track)
        return tracks

    async def insert_data(self,songs: list[Song]) -> None:
        await self.database.connection.executemany("""
             INSERT OR IGNORE INTO songs (song_name,full_path,parent_catalog,duration,artist) 
             VALUES (:song_name,:full_path,:parent_catalog,:duration,:artist)""",
                    [vars(s) for s in songs],)
        await self.database.connection.commit()
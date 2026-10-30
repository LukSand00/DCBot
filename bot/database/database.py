import aiosqlite
import os

class Database:
    # CONSTANT USED AS ESCAPE CHARACTER IN SQL QUERIES
    ESCAPE_CHARACTER = '|'
    # LIST OF CHARACTERS THAT NEED TO BE ESCAPED IN VALUES USED FOR QUERIES
    # DO NOT PUT ESCAPE_CHARACTER HERE
    CHARS_TO_ESCAPE = ('%','_')

    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None

    async def connect(self):
        if self.connection is not None:
            raise RuntimeError('Database already connected.')
        if not os.path.exists(self.db_path):
            raise FileNotFoundError('Database does not exist. Run initialize_database.py script first.')
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

    async def search_songs(self, song_name: str):
        if self.connection is None:
            raise RuntimeError('Database is not connected.')
        adjusted_name = f"%{Database.escape_characters(song_name)}%"
        async with self.connection.execute("""
                                           SELECT song_name, full_path, duration FROM songs
                                           WHERE song_name LIKE ? ESCAPE ? 
                                           ORDER BY song_name LIMIT 11""", (adjusted_name,Database.ESCAPE_CHARACTER,),) as cursor:
            rows = await cursor.fetchall()
        return rows

    @classmethod
    def escape_characters(cls,song_name: str):
        escape_char = cls.ESCAPE_CHARACTER
        escaped_name = song_name.replace(escape_char, escape_char + escape_char)
        for char in cls.CHARS_TO_ESCAPE:
            escaped_name = escaped_name.replace(char,escape_char + char)
        return escaped_name

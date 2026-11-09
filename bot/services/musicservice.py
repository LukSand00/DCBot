import os
from models.song import Song

class MusicPlayerService:
    DISPLAY_LIMIT = 10
    QUEUE_LIMIT = int(os.environ.get("MUSIC_QUEUE_LIMIT"))
    MINIMAL_QUERY_LENGTH = 5

    def __init__(self, guild_id, db_pool):
        self.guild_id: int = guild_id
        self.db_pool = db_pool
        self.queue: list[Song] = []
        self.current_song: Song = None

    async def get_songs(self, song_name) -> list[Song]:
        if len(song_name) < self.MINIMAL_QUERY_LENGTH:
            raise ValueError(f"Minimal query length is {self.MINIMAL_QUERY_LENGTH} characters.")
        song_list = await self.db_pool.fetch_songs(song_name=song_name)
        return song_list

    def validate_list(self, song_list: list[Song]) -> Song:
        if len(song_list) == 0:
            raise ValueError('Song not found.')
        elif len(song_list) > self.DISPLAY_LIMIT:
            raise ValueError('Too many songs found. Narrow your query.')
        elif 1 < len(song_list):
            raise ValueError('Pick one of the songs.')
        else:
            song = song_list.pop(0)
            return song

    def dequeue_song(self) -> Song:
        song = self.queue.pop(0)
        return song

    def enqueue_song(self, song: Song) -> None:
        if len(self.queue) < self.QUEUE_LIMIT:
            self.queue.append(song)
            return
        else:
            raise ValueError('Queue is full.')

    def clear_queue(self) -> None:
        self.queue.clear()

class MusicPlayerManager:
    def __init__(self):
        self.players: dict = {}

    def get_player(self, guild_id: int, db_pool=None) -> MusicPlayerService:
        if guild_id not in self.players:
            self.players[guild_id] = MusicPlayerService(guild_id, db_pool)
            return self.players[guild_id]
        return self.players[guild_id]

    def has_player(self, guild_id: int) -> bool:
        if guild_id not in self.players:
            return False
        return True

    def remove_player(self, guild_id: int) -> None:
        if guild_id in self.players:
            del self.players[guild_id]

mpm = MusicPlayerManager()
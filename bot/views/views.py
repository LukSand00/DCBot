import discord
from discord import user
from models.song import Song

class SongListView(discord.ui.View):
    message: discord.Message | None = None
    count = 0

    def __init__(self, author, songs: list[Song],*, timeout: float = 30.0) -> None:
        super().__init__(timeout=timeout)
        self.author = author
        self.choice: Song | None = None
        self.message: discord.Message | None = None
        for song in songs:
            self.add_item(SongButton(song))

    async def interaction_check(self, interaction: discord.Interaction[discord.Client]) -> bool:
        if interaction.user == self.author:
            return True
        return False

    async def on_timeout(self) -> None:
        for button in self.children:
            button.disabled = True
        if self.message:
            await self.message.edit(view=self)

class SongButton(discord.ui.Button):
    def __init__(self, song: Song) -> None:
        super().__init__(label=str(song.song_name), style=discord.ButtonStyle.primary)
        self.song = song

    async def callback(self, interaction: discord.Interaction) -> None:
        view: SongListView = self.view
        view.choice = self.song
        await interaction.response.defer()
        view.stop()

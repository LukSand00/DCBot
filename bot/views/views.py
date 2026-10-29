import discord
from discord import user


class SongListView(discord.ui.View):
    message: discord.Message | None = None
    count = 0

    def __init__(self, user: discord.User | discord.Member, timeout: float = 30.0) -> None:
        super().__init__(timeout=timeout)
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction[discord.Client]) -> bool:
        if interaction.user == self.user:
            return True
        return False

    async def on_timeout(self) -> None:
        for button in self.children:
            button.disabled = True

        if self.message:
            await self.message.edit(view=self)


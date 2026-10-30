import os
import asyncio

from dotenv import load_dotenv
import discord
from discord.ext import commands

from database.database import Database

load_dotenv()

INITIAL_COGS = [
    "cogs.music",
]

class Bot(commands.Bot):
    def __init__(self, database: Database):
        self.database = database
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix = '!',
            intents=intents,
        )

    async def setup_hook(self) -> None:
        for cog in INITIAL_COGS:
            try:
                await self.load_extension(cog)
            except Exception as e:
                print(f"Failed to load extension {cog}. Reason: {e}", flush=True)
        await self.tree.sync()

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}")

async def main() -> None:
    discord.utils.setup_logging()
    database = Database(os.environ['DATABASE_PATH'])
    await database.connect()
    bot = Bot(database=database)
    try:
        await bot.start(os.environ["DISCORD_TOKEN"])
    finally:
        await database.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
import asyncio
from collections import deque

import discord
from discord.ext import commands

class Music(commands.Cog):

    DISPLAY_LIMIT = 10

    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.queue = {}

    @commands.Cog.listener()
    async def join(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author

    @commands.command()
    async def play(self, ctx, *, query):

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        # PRZEROBIĆ LAMBDE NA OSOBNĄ METODE

        ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Now playing: {query}')

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send('You are not connected to a voice channel.')
                raise commands.CommandError('Author not connected to a voice channel.')
        elif ctx.voice_client.is_playing():
            # LOGIKA DODAWANIA PIOSENEK DO KOLEJKI
            ctx.voice_client.stop()
import asyncio
from collections import deque
from bot.database.database import Database
from bot.views.views import SongListView

import discord
from discord.ext import commands

class Music(commands.Cog):

    DISPLAY_LIMIT = 10

    def __init__(self, bot, database: Database):
        self.bot = bot
        self._last_member = None
        self.database = database
        self.queue = []

    @commands.Cog.listener()
    async def join(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author

    @commands.command()
    async def play(self, ctx, *, query):
        song_list = await self.database.search_songs(query)
        if len(song_list) == 0:
            await ctx.send('Song not found.')
            return
        elif len(song_list) > self.DISPLAY_LIMIT:
            await ctx.send('Found many results. Narrow down your query.')
            return
        elif 1 < len(song_list):
            names_text = '\n'.join(n['song_name'] + '\n' for n in song_list)
            await ctx.send('Multiple results. Pick from list below.\n' + names_text)
            return
        song = song_list[0]
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            self.queue.append(song)
            await ctx.send('Song added to queue.')
        else:
            await self.play_song(ctx, song)
        return

    async def choose_song(self,ctx,song_list):
        view = SongListView(ctx.author)
        for song in song_list:
            view.add_item(discord.ui.Button(label=song["song_name"], style=discord.ButtonStyle.primary))
        view.message = await ctx.send("Multiple results. Pick from the list.", view=view)

    async def play_song(self,ctx, song):
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song['full_path']))
        ctx.voice_client.play(source, after=lambda error: self.track_finished(ctx, error))
        await ctx.send(f'Now playing: {song["song_name"]}. ' + Music.format_duration(song['duration']))

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send('You are not connected to a voice channel.')
                raise commands.CommandError('Author not connected to a voice channel.')

        #elif ctx.voice_client.is_playing():
        #    LOGIKA DODAWANIA PIOSENEK DO KOLEJKI
        #    ctx.voice_client.stop()

    def track_finished(self, ctx, error):
        if error:
            print(f'Player error: {error}')
        if self.queue:
            song = self.queue.pop(0)
            self.play_song(ctx,song)


    @staticmethod
    def format_duration(duration):
        if duration is None:
            return 'Unknown length.'
        else:
            minutes, seconds = divmod(duration, 60)
            return f'Duration: {minutes}:{seconds}.'

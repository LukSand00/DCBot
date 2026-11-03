import os
import asyncio
from typing import Optional
from views.views import SongListView
from services.downloader import Downloader

import discord
from discord.ext import commands

from services.downloader import Downloader, DownloadFailed


class Music(commands.Cog):

    DISPLAY_LIMIT = 10
    QUEUE_LIMIT = int(os.environ.get("MUSIC_QUEUE_LIMIT"))
    MINIMAL_QUERY_LENGTH = 5

    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.downloader = Downloader()
        self.queue = []

    class SearchFlags(commands.FlagConverter):
        title: Optional[str] = None
        type: Optional[str] = None

    @commands.Cog.listener()
    async def join(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def play(self, ctx, *, query):
        song_list = await self.bot.database.search_songs(query)
        song = await self._validate_list(ctx, song_list)
        await self._enqueue_or_play(ctx, song)

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def playt(self, ctx, *, yturl):
        try:
            song = await self.downloader.download(yturl)
        except DownloadFailed as e:
            await ctx.send(f"{e}")
            return
        await self._enqueue_or_play(ctx, song)

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def pause(self,ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send('Paused.')
        else:
            await ctx.send('Bot is already paused.')

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def resume(self,ctx):
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send('Resumed.')
        else:
            await ctx.send('Bot is already playing.')

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def skip(self, ctx):
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            await ctx.send('Skipping.')
            ctx.voice_client.stop()

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def leave(self, ctx):
        if ctx.voice_client:
            self.queue.clear()
            ctx.voice_client.stop()

    @play.before_invoke
    @playt.before_invoke
    async def ensure_voice_or_join(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send('You are not connected to a voice channel.')
                raise commands.CheckFailure('Author not connected to a voice channel.')

    @pause.before_invoke
    @resume.before_invoke
    @skip.before_invoke
    async def ensure_bot_connected(self, ctx):
        if ctx.voice_client is None:
            await ctx.send('Bot is not connected to a voice channel.')
            raise commands.CheckFailure('Bot is not connected to a voice channel.')

    async def _validate_list(self, ctx, song_list):
        if len(song_list) == 0:
            await ctx.send('Song not found.')
            return None
        elif len(song_list) > self.DISPLAY_LIMIT:
            await ctx.send('Found many results. Narrow down your query.')
            return None
        elif 1 < len(song_list):
            song = await self._choose_song(ctx, song_list)
            return song
        else:
            song = song_list[0]
            return song

    async def _enqueue_or_play(self, ctx, song):
        if not song:
            return
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            if len(self.queue) <= self.QUEUE_LIMIT:
                self.queue.append(song)
                await ctx.send('Song added to queue.')
            else:
                await ctx.send(f'Reached queue limit of {Music.QUEUE_LIMIT}.')
        else:
            await self._play_song(ctx, song)
        return

    async def _play_song(self,ctx, song):
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song.full_path))
        ctx.voice_client.play(source, after=lambda error: self._track_finished(ctx, error))
        await ctx.send(f'Now playing: {song.song_name}. ' + song.format_duration())

    async def _choose_song(self,ctx,song_list):
        lines = "Choose song from the list:\n"
        view = SongListView(author=ctx.author, songs=song_list)
        view.message = await ctx.send(lines, view=view)
        await view.wait()
        if view.choice is None:
            return await ctx.send("Timed out.")
        else:
            return view.choice

    def _track_finished(self, ctx, error):
        if error:
            print(f'Player error: {error}', flush=True)
            return None
        self.downloader.clear_directory()
        if self.queue:
            song = self.queue.pop(0)
            fut = asyncio.run_coroutine_threadsafe(self._play_song(ctx=ctx,song=song), self.bot.loop)
        else:
            fut = asyncio.run_coroutine_threadsafe(self._finished_playing(ctx=ctx), self.bot.loop)
        fut.result()
        return None

    async def _finished_playing(self, ctx):
        await ctx.send('Finished playing.')
        await ctx.voice_client.disconnect()


async def setup(bot):
    await bot.add_cog(Music(bot))
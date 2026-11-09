import os
import asyncio
from typing import Optional
from urllib.parse import urlparse

from views.views import SongListView
from services.downloaderservice import DownloaderService, DownloadFailed
from services.musicservice import mpm

import discord
from discord.ext import commands


class Music(commands.Cog):

    DISPLAY_LIMIT = 10
    MINIMAL_QUERY_LENGTH = 5

    def __init__(self, bot):
        self.bot = bot
        self.downloaderService = DownloaderService()

    class SearchFlags(commands.FlagConverter):
        title: Optional[str] = None
        type: Optional[str] = None

    @staticmethod
    def _is_url(query: str) -> bool:
        parsed = urlparse(query)
        if parsed.scheme in ['http', 'https'] and parsed.netloc:
            return True
        return False

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def play(self, ctx, *, query) -> None:
        try:
            song_player = mpm.get_player(ctx.guild.id, self.bot.database)
            song_list = await song_player.get_songs(song_name=query)
            song = song_player.validate_list(song_list=song_list)
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                song_player.enqueue_song(song=song)
                await ctx.send('Song added to queue.')
                return
        except ValueError as e:
            await ctx.send(f"{e}")
            return
        await self._play_song(ctx, song)

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def playt(self, ctx, *, query) -> None:
        try:
            song_player = mpm.get_player(ctx.guild.id, self.bot.database)
            if self._is_url(query):
                song = await self.downloaderService.download(url=query)
            else:
                song_list = await self.downloaderService.search_video(query=query)
                song = await self._choose_song(ctx, song_list=song_list)
                if song:
                    song = await self.downloaderService.download(url=song.yt_url, song=song)
                pass
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                song_player.enqueue_song(song=song)
                await ctx.send('Song added to queue.')
                return
        except DownloadFailed as e:
            await ctx.send(f"Error encountered while downloading. {e}")
            return
        await self._play_song(ctx, song)

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def pause(self,ctx) -> None:
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send('Paused.')
        else:
            await ctx.send('Bot is already paused.')

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def resume(self,ctx) -> None:
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send('Resumed.')
        else:
            await ctx.send('Bot is already playing.')

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def skip(self, ctx) -> None:
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            await ctx.send('Skipping.')
            ctx.voice_client.stop()

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def queue(self, ctx) -> None:
        if ctx.music_player.queue:
            songs = "\n".join([song.song_name for song in ctx.music_player.queue])
            await ctx.send(songs)
        else:
            await ctx.send('Queue is empty.')

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def clear_queue(self, ctx) -> None:
        ctx.music_player.clear_queue()
        await ctx.send('Queue cleared.')

    @commands.command()
    @commands.has_role(os.environ.get('MUSIC_ROLE_ID'))
    async def leave(self, ctx) -> None:
        if ctx.voice_client:
            self.queue.clear()
            ctx.voice_client.stop()

    @play.before_invoke
    @playt.before_invoke
    async def ensure_voice_or_join(self, ctx) -> None:
        if ctx.voice_client is None:
            if ctx.author.voice:
                ctx.music_player = mpm.get_player(ctx.guild.id, self.bot.database)
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send('You are not connected to a voice channel.')
                raise commands.CheckFailure('Author not connected to a voice channel.')

    @pause.before_invoke
    @resume.before_invoke
    @skip.before_invoke
    async def ensure_bot_connected(self, ctx) -> None:
        if ctx.voice_client is None:
            await ctx.send('Bot is not connected to a voice channel.')
            raise commands.CheckFailure('Bot is not connected to a voice channel.')

    @queue.before_invoke
    @clear_queue.before_invoke
    async def ensure_queue(self,ctx) -> None:
        if mpm.has_player(ctx.guild.id):
            ctx.music_player = mpm.get_player(ctx.guild.id)
        else:
            await ctx.send('There is no player connected to server.')
            raise commands.CheckFailure('There is no player connected to server.')

    async def _play_song(self,ctx, song) -> None:
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song.full_path))
        ctx.voice_client.play(source, after=lambda error: self._track_finished(ctx, song, error))
        await ctx.send(f'Now playing: {song.song_name}. ' + song.format_duration())

    async def _choose_song(self,ctx,song_list):
        lines = "Choose song from the list:\n"
        view = SongListView(author=ctx.author, songs=song_list)
        view.message = await ctx.send(lines, view=view)
        await view.wait()
        if view.choice is None:
            await view.message.delete()
            await ctx.send("Timed out.")
            raise commands.CheckFailure('View timed out.')
        else:
            await view.message.delete()
            return view.choice

    def _track_finished(self, ctx, song, error):
        if error:
            print(f'Player error: {error}', flush=True)
            return None
        if song.source == 'yt':
            self.downloaderService.delete_temp(song.full_path)
        player = mpm.get_player(ctx.guild.id)
        if player.queue:
            song = player.dequeue_song()
            fut = asyncio.run_coroutine_threadsafe(self._play_song(ctx=ctx,song=song), self.bot.loop)
        else:
            self.downloaderService.clear_directory()
            fut = asyncio.run_coroutine_threadsafe(self._finished_playing(ctx=ctx), self.bot.loop)
        fut.result()
        return None

    async def _finished_playing(self, ctx):
        await ctx.send('Finished playing.')
        mpm.remove_player(ctx.guild.id)
        await ctx.voice_client.disconnect()


async def setup(bot):
    await bot.add_cog(Music(bot))
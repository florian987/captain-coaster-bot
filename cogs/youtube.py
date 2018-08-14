from discord.ext import commands
import discord
import youtube_dl
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
import re
import os

log = logging.getLogger(__name__)

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': os.path.join('yt_dls', '%(extractor)s-%(id)s-%(title)s.%(ext)s'),
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    # Placeholder
    @staticmethod
    async def get_url(query, *, playlist=False, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.youtube.com/results?search_query=" + query) as r:
                html = await r.read()
                #print(html)
                urls = []
                soup = BeautifulSoup(html, "html.parser")
                for vid in soup.findAll('a', href=re.compile("watch")):
                    urls.append('https://www.youtube.com' + vid['href'])
                #print(urls)
                if playlist:
                    return urls
                else:
                    return urls[0]
        
    @classmethod
    async def from_search(cls, query, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        #self.from_url
        url = await cls.get_url(query)
        print(url)
        await cls.from_url(url, loop=None)
        
        #data = await loop.run_in_executor(None, lambda: ytdl.extract_info(urls[0], download=not stream))
        #if 'entries' in data:
        #    # take first item from a playlist
        #    data = data['entries'][0]
        #filename = data['url'] if stream else ytdl.prepare_filename(data)
        #return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)



class Youtube_Commands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, query):
        """Plays a file from the local filesystem"""

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(query))

    @commands.command()
    async def yt(self, ctx, *, url):
        """Plays from a url (almost anything youtube_dl supports)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command()
    async def stream(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command()
    async def volume(self, ctx, volume: float):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume
        await ctx.send("Changed volume to {}%".format(volume))

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        log.info(f"Disconnected from voice channel '{ctx.voice_client.channel}' by '{ctx.author}'.")
        await ctx.voice_client.disconnect()

    @commands.command(name='comeplay', aliases=['playhere', 'joinplay'])
    async def comeplay(self, ctx, *, arg):
        "Play the desired song in your Voice Channel"

        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
        else:
            await ctx.author.voice.channel.connect()

        if arg.startswith('http'):
            async with ctx.typing():
                player = await YTDLSource.from_url(arg, loop=self.bot.loop, stream=False)
                ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
        else:
            async with ctx.typing():
                url = await YTDLSource.get_url(arg)
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=False)
                #player = await YTDLSource.from_search(arg, loop=self.bot.loop, stream=False)
                ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
            #return

        await ctx.send('Now playing: {}'.format(player.title))



    #
    # BEFORE / AFTER 
    #

    @play.before_invoke
    @yt.before_invoke
    @stream.before_invoke
    @comeplay.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

    # Use an existing command
    #def disconnect(self, ctx):
    #    await ctx.voice_client.disconnect()
#
    #@play.after_invoke
    #async def after_play_command(self, ctx):
    #    self.disconnect(ctx)
    #    pass


    #
    # ERROR HANDLER
    #
    @comeplay.error
    async def comeplay_handler(self, ctx, error):
        # Check if our required argument is missing.
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Provide an url to play sir!")

    @volume.error
    async def volume_handler(self, ctx, error):
        # Check if our required argument is missing.
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Volume: {ctx.voice_client.source.volume}%")
            

def setup(bot):
    bot.add_cog(Youtube_Commands(bot))

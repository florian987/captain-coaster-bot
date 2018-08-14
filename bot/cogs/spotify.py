from discord.ext import commands
import discord
import spotipy


class Spotify_Commands:
    def __init__(self, bot):
        self.bot = bot
        self.spotify = spotipy.Spotify()

    @commands.group(name='spotify', aliases=['sptf'])
    @commands.guild_only()
    #@commands.has_role(config['users'])
    async def spotify(self, ctx):
        """Interact with spotify"""

        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid config command passed...')


    @spotify.command(name='play', aliases=[])
    @commands.guild_only()
    async def play_song(self, ctx, *, args):


        title = None
        text = None
        embed = discord.Embed(
            title=title,
            description=text,
            colour=ctx.author.colour)
        embed.set_author(icon_url=ctx.author.avatar_url,
                         name=str(ctx.author))
        await ctx.send(content='', embed=embed)


def setup(bot):
    bot.add_cog(Spotify_Commands(bot))

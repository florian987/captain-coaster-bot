from discord.ext import commands
import discord
import aiohttp


class VRS_Commands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="get_channels", aliases=["get_chans",'get_setups_chans','get_setups_channels'])
    @commands.guild_only()
    async def get_channels(self, ctx):
        """ Build setups channels list"""

        channels_setups = []
        for channel in self.bot.get_all_channels():
            if channel.category:
                if channel.category.name == "Setups":
                    channels_setups.append(channel)
        
        for channel in channels_setups:
            print(channel.name)
        
        await ctx.send(','.join(channel.name for channel in channels_setups))

        

    @commands.command(name="setups", aliases=["vrs-setups"])
    @commands.guild_only()
    async def setups(self, ctx):
        """Retrieve cars setups from Virtual Racing School Website"""

        # Check if VRS is online
        async with aiohttp.ClientSession() as session:
            async with session.get('https://virtualracingschool.appspot.com/#/DataPacks') as r:
                if r.status == 200:
                    online = True
                else:
                    online = False

        if online:
            title = "VRS est Online!"
            text = "On va faire péter les sets"
            colour = discord.Colour.green()
        else:
            title = "VRS Offline :("
            text = "Va falloir attendre mon mignon"
            colour = discord.Colour.red()
        
        embed = discord.Embed(
            title=title,
            description=text,
            colour=colour)
        embed.set_author(icon_url=self.bot.user.avatar_url,
                        name=str(self.bot.user.name))
        await ctx.send(content='', embed=embed)


def setup(bot):
    bot.add_cog(VRS_Commands(bot))

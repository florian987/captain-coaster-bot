from discord.ext import commands
import discord
import aiohttp
import os

try:
    import scrapper.settings
    import scrapper.scrapper as scrapper
except ModuleNotFoundError:
    import cogs.scrapper.settings
    import cogs.scrapper.scrapper as scrapper
except:
    print('Can not import scrapper modules')

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
        
        print(os.path.dirname(os.path.realpath(__file__)))
        print(scrapper.get_path())

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

        # Build cars infos
        if online:
            # retrieve discord channels list
            setup_channels = []
            for channel in self.bot.get_all_channels():
                if channel.category:
                    if channel.category.name == "Setups":
                        setup_channels.append(channel)
        
            for channel in setup_channels:
                print(channel.name)

            # Change Bot Status    
            await self.bot.change_presence(activity=discord.Game(name='Lister les setups'))

            # Scrap VRS
            iracing_cars = scrapper.build_cars_list()

            # Change Bot Status    
            await self.bot.change_presence(activity=discord.Game(name='Récupérer les setups'))
            cars_list = scrapper.build_datapacks_infos(iracing_cars)

            for car in cars_list:
                title = car['serie']
                text = car['name']
                img = car['img_url']

                embed = discord.Embed(
                    title=title,
                    description=text,
                    colour=ctx.author.colour)
                    
                embed.set_image(url=img)

                embed.set_author(icon_url=self.bot.user.avatar_url,
                                name=str(self.bot.user.name))
                await ctx.send(content='', embed=embed)

            #title = "VRS est Online!"
            #text = "On va faire péter les sets"
            #colour = discord.Colour.green()
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

        # Change Bot Status    
        await self.bot.change_presence(activity=discord.Game(name='Enfiler des petits enfants'))
            

def setup(bot):
    bot.add_cog(VRS_Commands(bot))

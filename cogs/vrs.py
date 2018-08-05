from discord.ext import commands
import discord
import aiohttp
import os
import json

try:
    import utils
except:
    import cogs.utils

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
        
        #for channel in channels_setups:
        #    print(channel.name)

        await ctx.send(','.join(channel.name for channel in channels_setups))
        await ctx.send(','.join(channel.id for channel in channels_setups))



        

    @commands.command(name="setups", aliases=["vrs-setups"])
    @commands.guild_only()
    async def setups(self, ctx):
        """Retrieve cars setups from Virtual Racing School Website"""

        setups_category_name = "Setups"
        upload_channel_name = "__uploads__"

        #def retrieve_channel(channel_name, channel_category='Setups'):
        #    if any(channel.name == channel_name.lower() for channel in setup_channels):
        #            return channel
        #        else:
        #            print(serie_channel_name, 'not in channel, creating')
        #            serie_channel = await ctx.guild.create_text_channel(serie_channel_name, category=setups_category)

        # Check if VRS is online
        async with aiohttp.ClientSession() as session:
            async with session.get('https://virtualracingschool.appspot.com/#/DataPacks') as r:
                if r.status == 200:
                    online = True
                else:
                    online = False


        # Build channels list
        channels_setups = []
        for channel in self.bot.get_all_channels():
            if channel.category and channel.category.name == setups_category_name:
                channels_setups.append(channel)

        # Build cars infos
        if online:
            # retrieve discord channels list
            setup_channels = []
            for channel in self.bot.get_all_channels():
                if channel.category and channel.category.name == setups_category_name:
                    setup_channels.append(channel)

            # Retrieve desired category_id
            for category in ctx.guild.categories:
                if category.name == setups_category_name:
                    setups_category = category



            driver = scrapper.build_driver(headless=True)

            # Change Bot Status    
            #await self.bot.change_presence(activity=discord.Game(name='Lister les setups'))

            # Scrap VRS
            iracing_cars = scrapper.build_cars_list(driver)

            # Build datapacks in async
            cars_list = await self.bot.loop.run_in_executor(None, scrapper.build_datapacks_infos, driver, iracing_cars)

            print('End of datapacks building')
            print(cars_list)
            
            # Change Bot Status    
            #await self.bot.change_presence(activity=discord.Game(name='Récupérer les setups'))
            #cars_list = scrapper.build_datapacks_infos(driver, iracing_cars)

            # Ensure upload channel exists
            #if car['serie'].replace(' ','-') not in setup_channels:
            if any(channel.name == upload_channel_name.lower() for channel in setup_channels):
                upload_channel = channel
            else:
                print(upload_channel_name, 'not in channel, creating')
                upload_channel = await ctx.guild.create_text_channel(upload_channel_name, category=setups_category)

            async def is_file_uploaded(filename_on_discord):
                if upload_channel.history():
                    async for message in upload_channel.history():
                        if message.content == filename_on_discord:
                            return True
                return False

            async def get_upload_message(filename_on_discord):
                async for message in upload_channel.history():
                    if message.content == filename_on_discord:
                        return message


            for car in cars_list:

                print(json.dumps(car, indent=4))

                # Check if channel exists and create it
                serie_channel = None
                upload_channel = None

                serie_channel_name = car['serie'].replace(' ','-')

                # Ensure serie channel exists
                if any(channel.name == serie_channel_name.lower() for channel in setup_channels):
                    serie_channel = channel
                else:
                    print(serie_channel_name, 'not in channel, creating')
                    serie_channel = await ctx.guild.create_text_channel(serie_channel_name, category=setups_category)



                for datapack in car['datapacks']:
                    for file in datapack['files']:
                        filename_on_discord = car['serie'].replace(' ','_') + '-' + car['name'].replace(' ','_') + '-' + datapack['track'].replace(' ','_') + '-' + file['name']

                        # Search for uploaded file in upload channel        
                        #upload_history = await upload_channel.history()
                        #file_uploaded = discord.utils.find(lambda message: message.content == filename_on_discord, upload_history)
                        #async for message in upload_channel.history():
                        #    if message.content == filename_on_discord:
                        #        return True
                        

                        # upload file if not exists
                        #if not file_uploaded:
                        if not await is_file_uploaded(filename_on_discord):
                            file_upload_msg = await upload_channel.send(content=filename_on_discord, file=discord.File(file['path']))
                            print(file_upload_msg)
                            uploaded_file = file_upload_msg.attachments[0]
                            print(uploaded_file) 
                            return uploaded_file

                        embed = utils.build_embed(
                                ctx, 
                                author_name=car['author'], 
                                author_avatar_url=car['img_author'],
                                title=car['serie'] + ' - ' + car['name'],
                                description=datapack['track'],
                                img_url=car['img_url'],
                                setup="[Download](https://www.google.com)")
                            
                        await ctx.send(content='', embed=embed)
                        # TODO retrieve file url if already uploaded
                        #else:
                        #    uploaded_file = await upload_channel.history().get(content=filename_on_discord)[0]
                        #    return uploaded_file


                            # Get attachment
                            

                        

                   # # Build embed
                   # title = car['serie']
                   # text = car['name']
                   # img = car['img_url']
#
                   # embed = discord.Embed(
                   #     title=title,
                   #     description=text,
                   #     colour=discord.Colour.red())                        
                   # embed.set_image(url=img)
                   # embed.set_author(icon_url=car['img_author'],
                   #                 name=car['author'])
#
                   # for file in datapack:
                   #     embed.add_field(name=file['type'], value=uploaded_file.url, inline=True)
                   # 
                   # await ctx.send(content='', embed=embed)
#
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
        #await self.bot.change_presence(activity=discord.Game(name='Enfiler des petits enfants'))
            


def setup(bot):
    bot.add_cog(VRS_Commands(bot))

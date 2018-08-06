from discord.ext import commands
import discord
import aiohttp
import os
import json

import cogs.custom_functions as tools
   

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


    @commands.command(name="flushsetups", aliases=['flushsets'], hidden=True)
    @commands.is_owner()
    async def flush_setups(self, ctx):
        """Flush VRS setups"""

        def is_me(m):
            return m.author == self.bot.user

        channels_setups = []
        for channel in self.bot.get_all_channels():
            if channel.category and channel.category.name == "Setups":
                channels_setups.append(channel)

        print('-' * 20)
        print(channels_setups)

        for channel in channels_setups:
            print('-' * 20)
            print(channel)
            deleted = await channel.purge(check=is_me)
            if deleted:
                await channel.send('Deleted {} message(s)'.format(len(deleted)))
                

        #await ctx.send('Deleted {} messages'.format(len(messages) + 1))
        

    @commands.command(name="setups", aliases=["vrs-setups"])
    @commands.guild_only()
    async def setups(self, ctx):
        """Retrieve cars setups from Virtual Racing School Website"""

        setups_category_name = "Setups"
        upload_channel_name = "__uploads__"

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

            # Ensure upload channel exists
            if any(channel.name == upload_channel_name.lower() for channel in setup_channels):
                upload_channel = discord.utils.get(ctx.guild.text_channels, name=upload_channel_name.lower())
            else:
                upload_channel = await ctx.guild.create_text_channel(upload_channel_name, category=setups_category)

            driver = scrapper.build_driver(headless=True)

            # Change Bot Status    
            await self.bot.change_presence(activity=discord.Game(name='Lister les setups'))

            # Scrap VRS
            iracing_cars = scrapper.build_cars_list(driver)

            # Build datapacks in async
            cars_list = await self.bot.loop.run_in_executor(None, scrapper.build_datapacks_infos, driver, iracing_cars)

            print('End of datapacks building')
            print(cars_list)
            
            # Change Bot Status    
            await self.bot.change_presence(activity=discord.Game(name='Récupérer les setups'))

            

            async def is_file_uploaded(filename_on_discord):
                if await upload_channel.history().get(content=filename_on_discord):
                    return True
                else:
                    return False

            async def get_upload_message(filename_on_discord):
                async for message in upload_channel.history():
                    if message.content == filename_on_discord:
                        return message


            for car in cars_list:

                print(json.dumps(car, indent=4))

                serie_channel_name = car['serie'].replace(' ','-')

                # Ensure serie channel exists
                if any(channel.name == serie_channel_name.lower() for channel in setup_channels):
                    serie_channel = discord.utils.get(ctx.guild.text_channels, name=serie_channel_name.lower())
                else:
                    serie_channel = await ctx.guild.create_text_channel(serie_channel_name, category=setups_category)



                for datapack in car['datapacks']:
                    if datapack['files']:
                        # Build embed
                        embed = discord.Embed()
                        embed.title = car['serie'] + ' - ' + car['name']
                        embed.description = datapack['track']
                        embed.set_image(url=car['img_url'])
                        embed.set_author(
                            icon_url = car['img_author'],
                            name = car['author']
                        )

                        for file in datapack['files']:
                            print('-' * 20)
                            print('file: ', file)
                            # TODO check filesize
                            filename_on_discord = car['serie'].replace(' ','_') + '-' + car['name'].replace(' ','_') + '-' + datapack['track'].replace(' ','_') + '-' + file['name']
                            
                            # upload file if not exists
                            if not await is_file_uploaded(filename_on_discord):
                                uploaded_file_msg = await upload_channel.send(content=filename_on_discord, file=discord.File(file['path']))
                            else:
                                uploaded_file_msg = await upload_channel.history().get(content=filename_on_discord) # utils.get

                            # Add file to embed
                            #embed.add_field(name=file['type'], value='[' + file['name'] + (' + uploaded_file_msg.attachments[0].url + ')')
                            embed.add_field(name=file['type'], value='[{}]({})]'.format(file['name'], uploaded_file_msg.attachments[0].url))
                        
                        # Send embed
                        await serie_channel.send(content='', embed=embed)

                        print('-' * 20)
                        print('End of loop')
                        print('-' * 20)
        
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

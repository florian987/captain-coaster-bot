from discord.ext import commands
import discord
import aiohttp
import os
import json

import cogs.custom_functions as tools
   
import cogs.scrapper.settings
import cogs.scrapper.scrapper as scrapper



class VRS_Commands:
    def __init__(self, bot):
        self.bot = bot


    


    @commands.command(name="get_setup_channels", aliases=["setup_chans",'get_setups_chans'])
    @commands.guild_only()
    async def get_channels(self, ctx):
        """ Build setups channels list"""
        # Retrieve setups categories
        setup_category = discord.utils.find(lambda c: c.name == "Setups", ctx.guild.categories)

        # Send message
        await ctx.send(','.join(channel.name for channel in setup_category.channels))
        await ctx.send(','.join(channel.id for channel in setup_category.channels))





    @commands.command(name="flushsetups", aliases=['flushsets'], hidden=True)
    @commands.is_owner()
    async def flush_setups(self, ctx):
        """Flush VRS setups"""
        # Retrieve setups categories
        setup_category = discord.utils.find(lambda c: c.name == "Setups", ctx.guild.categories)

        def is_me(m):
            return m.author == self.bot.user

        purged_channels = 0
        purged_msgs = 0

        for channel in setup_category.channels:
            deleted = await channel.purge(check=is_me)
            if deleted:
                await channel.send('Deleted {} message(s)'.format(len(deleted)))
                purged_channels += 1
                purged_msgs += len(deleted)

        if purged_msgs > 0:
            await ctx.send(f"Purged {purged_msgs} in {purged_channels} channel(s).")
        else:
            await ctx.send("Nothing to purge.")
            
        




    @commands.command(name="setups", aliases=["vrs-setups"])
    @commands.guild_only()
    async def setups(self, ctx):
        """Retrieve cars setups from Virtual Racing School Website"""

        setups_category_name = "Setups"
        upload_channel_name = "__uploads__"

        setup_category = discord.utils.find(lambda c: c.name == setups_category_name, ctx.guild.categories)

        # Check if VRS is online
        async def is_vrs_online():
            async with aiohttp.ClientSession() as session:
                async with session.get('https://virtualracingschool.appspot.com/#/DataPacks') as r:
                    if r.status == 200:
                        return True
                    else:
                        return False


        async def message_exists(channel: discord.TextChannel, filename):
            """Search message content in a defined channel"""
            if await channel.history().get(content=filename):
                return True
            else:
                return False


        # TODO END THIS
        async def ensure_channel_exists(chan, cat: discord.CategoryChannel):
            """Ensure a channel exists and create it if needed before returning it"""
            if any(channel.name == chan for channel in cat.channels):
                return discord.utils.get(ctx.guild.text_channels, name=serie_channel_name.lower(), category=cat.name)
            else:
                return await ctx.guild.create_text_channel(serie_channel_name, category=cat.name)


        # Build cars infos
        if is_vrs_online():
            
            # Ensure upload channel exists
            #if any(channel.name == upload_channel_name.lower() for channel in setup_category.channels):
            #    upload_channel = discord.utils.get(ctx.guild.text_channels, name=upload_channel_name.lower())
            #else:
            #    upload_channel = await ctx.guild.create_text_channel(upload_channel_name, category=setup_category)
            upload_channel = ensure_channel_exists(upload_channel_name.lower(), setup_category)

            # Change Bot Status    
            await self.bot.change_presence(activity=discord.Game(name='Lister les setups'))

            # Create webdriver
            driver = scrapper.build_driver(headless=True)
            # Scrap VRS
            iracing_cars = scrapper.build_cars_list(driver)
            cars_list = await self.bot.loop.run_in_executor(None, scrapper.build_datapacks_infos, driver, iracing_cars)

            # Change Bot Status    
            await self.bot.change_presence(activity=discord.Game(name='Récupérer les setups'))




            for car in cars_list:


                serie_channel_name = car['serie'].replace(' ','-').lower()

                # Ensure serie channel exists
                #if any(channel.name == serie_channel_name.lower() for channel in setup_category.channels):
                #    serie_channel = discord.utils.get(ctx.guild.text_channels, name=serie_channel_name.lower())
                #else:
                #    serie_channel = await ctx.guild.create_text_channel(serie_channel_name, category=setup_category)
                serie_channel = ensure_channel_exists(serie_channel_name, setup_category)



                for datapack in car['datapacks']:
                    if datapack['files']:
                        # Build embed
                        embed = discord.Embed()
                        embed.title = car['serie'] + ' - ' + car['name']
                        embed.url = datapack['url']
                        embed.colour = discord.Colour(16777215)
                        embed.description = datapack['track']
                        embed.set_image(url=car['img_url'])
                        embed.set_author(
                            icon_url = car['img_author'],
                            name = car['author']
                        )

                        for file in datapack['files']:
                            print('-' * 20)
                            print('file: ', file)
                            if round(os.path.getsize(file['path']) / 1024) < 8192: # Check if filesize < 8MB
                                # TODO check filesize
                                filename_on_discord = car['serie'].replace(' ','_') + '-' + car['name'].replace(' ','_') + '-' + datapack['track'].replace(' ','_') + '-' + file['name']
                                
                                # upload file if not exists
                                if not await message_exists(upload_channel_name, filename_on_discord):
                                    uploaded_file_msg = await upload_channel.send(content=filename_on_discord, file=discord.File(file['path']))
                                else:
                                    uploaded_file_msg = await upload_channel.history().get(content=filename_on_discord) # utils.get

                                # Add file to embed
                                embed.add_field(name=file['type'], value='[{}]({})'.format(file['name'], uploaded_file_msg.attachments[0].url))
                        
                        # Send embed
                        await serie_channel.send(content='', embed=embed)

        
        else:
            """If VRS Offline"""
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

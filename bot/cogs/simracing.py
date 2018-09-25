# import json
import os
import zipfile

import aiohttp
import discord
from discord.ext import commands
from PIL import Image

import bot.scrapper.vrs as scrapper
from bot.constants import Channels
from bot.decorators import in_channel


class Simracing:
    def __init__(self, bot):
        self.bot = bot

# TODO replace with a minlevel local check, create decorator
#    async def __local_check(self, ctx):
#        return discord.utils.find(
#            lambda r: r.name == 'Les Pilotes', ctx.author.roles
#        )

    @staticmethod
    def extract_tga(file: discord.Attachment):
        """
        A helper method to extract tga files from zip.
        """

        tga_list = []
        dest = 'tmp'  # Extract destination

        zfile = zipfile.ZipFile(file)
        for file in zfile.namelist():
            if file.split('.')[1] == 'tga':
                zfile.extract(file, dest)
                tga_list.append(os.path.join(dest, file))

        return tga_list

    @staticmethod
    def tga_to_png(tga_file: discord.File):
        """
        A helper method to convert tga files to png.
        """

        print(tga_file)

        png_file = tga_file.replace('.tga', '.png')
        # convert to png
        img = Image.open(tga_file)
        img.save(png_file)
        os.unlink(tga_file)  # remove tga file

        return png_file

    @commands.command(name="get_setup_channels",
                      aliases=["setup_chans", 'get_setups_chans'])
    @commands.guild_only()
    # @commands.has_role(config['users'])
    async def get_channels(self, ctx):
        """Build setups channels list"""
        # Retrieve setups categories
        setup_category = discord.utils.find(
            lambda c: c.name == "Setups", ctx.guild.categories
        )

        # Send message
        await ctx.send(
            ','.join(channel.name for channel in setup_category.channels)
            .replace('_', r'\_'))

    @commands.command(name="flushsetups", aliases=['flushsets'], hidden=True)
    @commands.is_owner()
    async def flush_setups(self, ctx):
        """
        Flush VRS setups
        """
        # Retrieve setups categories
        setup_category = discord.utils.find(
            lambda c: c.name == "Setups", ctx.guild.categories)

        def is_me(m):
            return m.author == self.bot.user

        purged_channels = 0
        purged_msgs = 0

        for channel in setup_category.channels:
            deleted = await channel.purge(check=is_me)
            if deleted:
                await channel.send(
                    f'Deleted {len(deleted)} message(s)'
                )
                purged_channels += 1
                purged_msgs += len(deleted)

        if purged_msgs > 0:
            await ctx.send(
                f"Purged {purged_msgs} message(s) in "
                "{purged_channels} channel(s).")
        else:
            await ctx.send("Nothing to purge.")

    @commands.command(name="setups", aliases=["vrs-setups"])
    @commands.guild_only()
    # @commands.has_role(config['users'])
    async def setups(self, ctx):
        """
        Retrieve cars setups from VRS Website
        """

        vrs_url = 'https://virtualracingschool.appspot.com/#/DataPacks'
        setups_category_name = "Setups"
        upload_channel_name = "__uploads__"

        setup_category = discord.utils.find(
            lambda c: c.name == setups_category_name, ctx.guild.categories)

        # Check if VRS is online
        async def is_vrs_online():
            async with aiohttp.ClientSession() as session:
                async with session.get(vrs_url) as r:
                    if r.status == 200:
                        return True
                    return False

        async def message_exists(channel: discord.TextChannel, message):
            """Search message content in a defined channel"""
            return bool(channel.history().get(content=message))
            # old method
            # if await channel.history().get(content=message):
            #     return True
            # return False

        # async def embed_exists(channel: discord.TextChannel, embed):
        #    """Search message content in a defined channel"""
        #    if await channel.history().get(embed=embed):
        #        return True
        #    return False

        # TODO END THIS
        async def ensure_channel_exists(chan, cat: discord.CategoryChannel):
            """
            Ensure a channel exists and return it
            """
            chan_to_return = discord.utils.get(
                ctx.guild.text_channels, name=chan, category=cat
            )
            if chan_to_return:
                return chan_to_return
            return await ctx.guild.create_text_channel(name=chan, category=cat)

        # Build cars infos
        if is_vrs_online():

            upload_channel = await ensure_channel_exists(
                upload_channel_name.lower(), setup_category)

            # Change Bot Status
            await self.bot.change_presence(
                activity=discord.Game(name='Lister les setups')
            )

            # Create webdriver
            driver = scrapper.build_driver(headless=False)

            # Scrap VRS website and build cars infos
            iracing_cars = scrapper.build_cars_list(driver)

            # Build datapacks infos
            await ctx.send(content='Start building datapacks')
            cars_list = await self.bot.loop.run_in_executor(
                None, scrapper.build_datapacks_infos, driver, iracing_cars
            )
            await ctx.send(content='Datapcks ended')

            # Change Bot Status
            await self.bot.change_presence(
                activity=discord.Game(name='Récupérer les setups'))

            # Upload files to discord
            for car in cars_list:

                # Create serie channel name
                serie_channel_name = car['serie'].replace(' ', '-').lower()
                serie_channel = await ensure_channel_exists(serie_channel_name,
                                                            setup_category)

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
                            icon_url=car['img_author'],
                            name=car['author']
                        )

                        for file in datapack['files']:

                            # Check file size limit before upload (8Mb)
                            if round(os.path.getsize(
                                     file['path']) / 1024) < 8192:

                                # Set the filename for upload channel
                                filename_on_discord = (
                                    f"{car['serie']}-{car['name']}-"
                                    f"{datapack['track']}-{file['name']}"
                                ).replace(' ', '_')

                                # upload file if not exists
                                if not await message_exists(
                                    upload_channel,
                                    filename_on_discord
                                ):
                                    upload_msg = (
                                        await upload_channel
                                        .send(content=filename_on_discord,
                                              file=discord.File(file['path']))
                                    )
                                else:
                                    upload_msg = (
                                        await upload_channel
                                        .history()
                                        .get(content=filename_on_discord))

                                # Add file to embed
                                embed.add_field(
                                    name=file['type'],
                                    value=f"[{file['name']}]"
                                    f"({upload_msg.attachments[0].url})")

                        # TODO Validate this works
                        # Send embed
                        # if not await embed_exists(serie_channel, embed):
                        await serie_channel.send(content='', embed=embed)

        else:
            """
            If VRS Offline
            """
            title = "VRS Offline :("
            text = "Va falloir attendre mon mignon"
            colour = discord.Colour.red()

            embed = discord.Embed(
                title=title,
                description=text,
                colour=colour
            )
            embed.set_author(icon_url=self.bot.user.avatar_url,
                             name=str(self.bot.user.name)
                             )
            await ctx.send(content='', embed=embed)

        # Change Bot Status
        await self.bot.change_presence(
            activity=discord.Game(name='Enfiler des petits enfants')
        )

    @in_channel(Channels.skins)
    async def on_message(self, msg: discord.Message):
        """
        Generate embed from uploaded skins
        """
#        if ctx.channel == Channels.skins and ctx.message.attachments:
        if msg.attachments:
            for attachment in msg.attachments:
                print(attachment.filename)
                file_ext = attachment.filename.split('.')[1]
                if file_ext == 'zip':
                    await attachment.save(attachment.filename)
                    tga_files = await self.bot.loop.run_in_executor(
                        None, self.extract_tga, attachment.filename
                    )

                    for tga in tga_files:
                        png_file = await self.bot.loop.run_in_executor(
                            None, self.tga_to_png, tga
                        )

                        await msg.channel.send(file=discord.File(png_file))
                elif file_ext == 'tga':
                    await attachment.save(attachment.filename)
                    png_file = await self.bot.loop.run_in_executor(
                        None, self.tga_to_png, attachment.filename
                    )
                    await msg.channel.send(file=discord.File(png_file))


def setup(bot):
    bot.add_cog(Simracing(bot))

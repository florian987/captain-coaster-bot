import itertools
import logging
import os
import re
import zipfile

import aiohttp
import discord
from discord.ext import commands
from PIL import Image

import scrapper.vrs as scrapper
from bot.constants import Channels, Roles
from bot.decorators import in_channel, with_role

log = logging.getLogger(__name__)


class Simracing:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def extract_tga(archive: discord.Attachment):
        """A helper method to extract tga files from zip."""

        tga_list = []

        zfile = zipfile.ZipFile(archive)
        for file in zfile.namelist():
            if file.split('.')[1] == 'tga':
                zfile.extract(file)
                tga_list.append(file)
        zfile.close()
        os.unlink(archive)

        return tga_list

    @staticmethod
    def tga_to_png(tga_file: discord.File):
        """
        A helper method to convert tga files to png.
        """

        png_file = tga_file.replace('.tga', '.png')
        # convert to png
        img = Image.open(tga_file)
        img.save(png_file)
        os.unlink(tga_file)  # remove tga file

        return png_file

    # @staticmethod
    # async def upload_and_delete(msg: discord.Message, file_to_process):
    #     await msg.channel.send(file=discord.File(file_to_process))
    #     os.unlink(file_to_process)  # remove pngfile

    @commands.command(name="get_setup_channels",
                      aliases=["setup_chans", 'get_setups_chans'])
    @commands.guild_only()
    @with_role(Roles.pilotes)
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
    @commands.guild_only()
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
            deleted = await channel.purge(check=is_me, limit=9999)
            if deleted:
                await channel.send(
                    f'Deleted {len(deleted)} message(s)'
                )
                purged_channels += 1
                purged_msgs += len(deleted)

        if purged_msgs > 0:
            await ctx.send(
                f"Purged {purged_msgs} message(s) in "
                f"{purged_channels} channel(s)."
            )
            log.info(
                f"Purged {purged_msgs} message(s) in "
                f"{purged_channels} channel(s)."
            )
        else:
            await ctx.send("Nothing to purge.")

    @commands.command(name="setups", aliases=["vrs-setups"])
    @commands.guild_only()
    @with_role(Roles.pilotes)
    async def setups(self, ctx):
        """Retrieve cars setups from VRS Website"""

        vrs_url = 'https://virtualracingschool.appspot.com/#/DataPacks'
        setups_category_name = "Setups"
        upload_channel_name = "__uploads__"

        setup_category = discord.utils.find(
            lambda c: c.name == setups_category_name, ctx.guild.categories)

        log.info(f"{ctx.message.author} started a VRS setups gathering")

        # Check if VRS is online
        async def is_vrs_online():
            async with aiohttp.ClientSession() as session:
                async with session.get(vrs_url) as r:
                    if r.status == 200:
                        return True
                    log.error("VRS website offline, aborting.")
                    return False

        # async def message_exists(channel: discord.TextChannel, message: discord.Message):
        #     """Search message content in a defined channel"""
        #     return bool(channel.history().get(content=message))
#
        # async def embed_exists(channel: discord.TextChannel, embed: discord.Embed):
        #     """Search embed in a defined channel"""
        #     return bool(channel.history().get(embed=embed))

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
            log.info(f"Creating channel '{chan}' in category '{cat}'.")
            return await ctx.guild.create_text_channel(name=chan, category=cat)

        # Build cars infos
        if is_vrs_online():

            upload_channel = await ensure_channel_exists(
                upload_channel_name.lower(), setup_category)

            # TODO End cehck if exists            
            upload_msg_hist = await upload_channel.history().flatten()

            def file_uploaded(history, filename):
                for message in history:
                    if message.content == filename:
                        return message

            def embed_sent(history, embed):  # rename to embed_exists
                for message in history:
                    for mbd in message.embeds:
                        if mbd.title == embed.title and mbd.description == embed.description:
                            return mbd

            # Change Bot Status
            await self.bot.change_presence(
                activity=discord.Game(name='Lister les setups')
            )

            # Create webdriver
            driver = scrapper.build_driver(headless=True)

            # Scrap VRS website and build cars infos
            iracing_cars = scrapper.build_cars_list(driver)

            # Build datapacks infos
            await ctx.send(content='Start building datapacks')
            cars_list = await self.bot.loop.run_in_executor(
                None, scrapper.build_datapacks_infos, driver, iracing_cars
            )
            await ctx.send(content='Datapacks ended')

            # Change Bot Status
            await self.bot.change_presence(
                activity=discord.Game(name='Récupérer les setups'))

            # Upload files to discord
            for car in cars_list:

                # Create serie channel name
                serie_channel_name = re.sub(' +', ' ', car['serie'].lower().replace('iracing', '').strip().replace('-', '')).replace(' ', '-')
                serie_channel = await ensure_channel_exists(
                    serie_channel_name, setup_category)
                
                channel_embeds = await serie_channel.history().flatten()

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
                        if datapack['time_of_day']:
                            embed.add_field(name="Moment de la journée", value=datapack['time_of_day'], inline=False)
                        if datapack['track_state']:
                            embed.add_field(name="Etat de la piste", value=datapack['track_state'], inline=False)
                        if datapack['fastest_laptime']:
                            embed.add_field(name="Meileur temps", value=datapack['fastest_laptime'], inline=False)
                            
                        for file in datapack['files']:

                            # Check file size limit before upload (8Mb)
                            if round(os.path.getsize(
                                    file['path']) / 1024) < 8192:

                                # Set the filename for upload channel
                                filename_on_discord = (
                                    f"{car['serie']}-{car['name']}-"
                                    f"{datapack['track']}-{file['name']}"
                                ).replace(' ', '_')

                                upload_msg = file_uploaded(upload_msg_hist, filename_on_discord)

                                if upload_msg is None:
                                    upload_msg = (
                                        await upload_channel.send(
                                            content=filename_on_discord,
                                            file=discord.File(file['path'])))

                                # Add file to embed
                                embed.add_field(
                                    name=file['type'],
                                    value=f"[{file['name']}]"
                                    f"({upload_msg.attachments[0].url})")

                        # TODO Validate this works
                        embed_exists = embed_sent(channel_embeds, embed)

                        if not embed_exists:
                            await serie_channel.send(embed=embed)
                            log.info(f"Sent embed for {car['serie']} - {car['name']}.")

        else:
            """If VRS Offline"""
            embed = discord.Embed(
                title="VRS Offline :(",
                description="Va falloir attendre mon mignon",
                colour=discord.Colour.red()
            )
            embed.set_author(
                icon_url=self.bot.user.avatar_url, name=str(self.bot.user.name))

            await ctx.send(content='', embed=embed)

    @in_channel(Channels.skins)
    async def on_message(self, msg: discord.Message):
        """
        Generate embed from uploaded skins
        """

        for attachment in msg.attachments:
            # Get file extension
            file_ext = attachment.filename.split('.')[1]

            # Handle zip files
            if file_ext == 'zip':
                await attachment.save(attachment.filename)  # DL file

                # Extract zipfiles
                tga_files = await self.bot.loop.run_in_executor(
                    None, self.extract_tga, attachment.filename
                )

                # Convert files
                for tga_file in tga_files:

                    png_file = await self.bot.loop.run_in_executor(
                        None, self.tga_to_png, tga_file
                    )

                    # await upload_and_delete(msg, png_file)
                    await msg.channel.send(file=discord.File(png_file))
                    os.unlink(png_file)  # remove pngfile
                    # os.unlink(attachment.filename)  # remove zipfile
                    log.info(f"Preview generated {png_file} "
                             f"- uploader: {msg.author}")

            # Handle tga files
            elif file_ext == 'tga':
                await attachment.save(attachment.filename)

                png_file = await self.bot.loop.run_in_executor(
                    None, self.tga_to_png, attachment.filename
                )
                # await upload_and_delete(msg, png_file)
                await msg.channel.send(file=discord.File(png_file))
                os.unlink(png_file)
                log.info(f"Preview generated {png_file} "
                         f"- uploader: {msg.author}")


def setup(bot):
    bot.add_cog(Simracing(bot))

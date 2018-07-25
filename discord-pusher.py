# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import configparser
import logging

# Add commands
# https://discordpy.readthedocs.io/en/rewrite/ext/commands/commands.html


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


bot = commands.Bot(command_prefix='$')

@bot.command()
async def test(ctx, arg):
    await ctx.send(arg)

@bot.event()
async def on_ready(ctx):
    print('Logged on as {0}!'.format(ctx.user))
    print('Discord.py version {0}!'.format(discord.__version__))
    for channel in bot.get_all_channels():
        print(channel, channel.category_id)
    
    print(type(discord.CategoryChannel.channels))

@bot.event ()
async def on_message(ctx, message):
    print('Message from {0.author}: {0.content}'.format(message))

    # Define listening commands
    if str(message.content) == "!get_channels_list":
        for channel in bot.get_all_channels():
            print(channel, channel.category_id, channel.category)

        

bot.run('NDcwMTM2MzgzMzgyNjE4MTEy.DjR5_w.xy3XstdJdbRSpzKulOwIdFDf-xA')

# Inite URL
# https://discordapp.com/oauth2/authorize?client_id=470136383382618112&scope=bot&permissions=125952


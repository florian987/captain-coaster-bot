# -*- coding: utf-8 -*-
import discord
import configparser
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        print('Discord.py version {0}!'.format(discord.__version__))
        for channel in client.get_all_channels():
            print(channel, channel.category_id)
        
        print(type(discord.CategoryChannel.channels))
            
    async def on_message(self, message):
        print('Message from {0.author}: {0.content}'.format(message))

        # Define listening commands
        if str(message.content) == "!get_channels_list":
            for channel in client.get_all_channels():
                print(channel, channel.category_id)

        

client = MyClient()
client.run('NDcwMTM2MzgzMzgyNjE4MTEy.DjR5_w.xy3XstdJdbRSpzKulOwIdFDf-xA')

# Inite URL
# https://discordapp.com/oauth2/authorize?client_id=470136383382618112&scope=bot&permissions=125952


from discord.ext import commands
import discord
import os
import json


class Configs_Commands:
    def __init__(self, bot):
        self.bot = bot
    
    
    @commands.command(name='showconf', aliases=['displayconf'])
    @commands.is_owner()
    async def showconf(self, ctx):
        """Display Bot configuration"""
        print(dir(self.bot))
        print(dir(self.bot.user))
        print('name:', self.bot.user.name)
        print('avatar_url:', self.bot.user.avatar_url)
        print(self.bot.user)
        await ctx.send(f'name: {self.bot.user.name}, avatar_url: {self.bot.user.avatar_url}')


    @commands.command(name='saveconfig', aliases=['saveconf'])
    @commands.is_owner()
    async def config_save(self, ctx):
        """Save bot configuraiton into a json file"""

        cfg_file = 'config.json'

        settings = {}

        settings['name'] = self.bot.user.name
        settings['avatar_url'] = self.bot.user.avatar_url

        with open (cfg_file, 'w') as file:
            json.dump(settings, file)



        #title = None
        #text = None
        #embed = discord.Embed(
        #    title=title,
        #    description=text,
        #    colour=ctx.author.colour)
        #embed.set_author(icon_url=ctx.author.avatar_url,
        #                 name=str(ctx.author))
        await ctx.send("**`Config succesfully saved.`**")


def setup(bot):
    bot.add_cog(Configs_Commands(bot))

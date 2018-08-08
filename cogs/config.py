from discord.ext import commands
import discord
import os
import json


class Configs_Commands:
    def __init__(self, bot):
        self.bot = bot
        self.config = 'config.json'

    #@bot.event
    #async def on_ready():
    
    @commands.group(name='conf', aliases=['config','settings'])
    @commands.is_owner()
    async def conf(self, ctx):
        """Manage bot configuration"""
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid config command passed...')


    @conf.command(name='show', aliases=['display','print'])
    @commands.is_owner()
    async def showconf(self, ctx):
        """Display Bot configuration""" 
        if os.path.isfile(self.config):
            with open(self.config, 'r') as file:
                settings = json.load(file)
            await ctx.send('```json\n' + json.dumps(settings, indent=4) + '\n```')


    @conf.command(name='save', aliases=['register'])
    @commands.is_owner()
    async def saveconfig(self, ctx):
        """Save bot configuration"""
        settings = {}
        settings['name'] = self.bot.user.name
        settings['avatar_url'] = self.bot.user.avatar_url
        with open (self.config, 'w') as file:
            json.dump(settings, file)
        await ctx.send("**`Config succesfully saved.`**")


    @conf.group(name='set', aliases=['change'])
    @commands.is_owner()
    async def set(self, ctx):
        """Change bot parameters"""
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid config command passed...')

    @set.command(name='username', aliases=['nick','pseudo','nickname','name'])
    @commands.is_owner()
    async def username(self, ctx, name):
        """Change bot username"""
        await self.bot.user.edit(username=name)

def setup(bot):
    bot.add_cog(Configs_Commands(bot))

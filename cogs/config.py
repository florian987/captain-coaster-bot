from discord.ext import commands
import discord
import os
import json
import aiohttp
import io
import logging

log = logging.getLogger(__name__)


class Configs_Commands:
    def __init__(self, bot):
        self.bot = bot
        #self.config = 'config.json'

    
    @commands.group(name='conf', aliases=['config','settings'])
    @commands.is_owner()
    async def conf(self, ctx):
        """Manage bot configuration"""
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid config command passed...')


    # Comment because useless
    #@conf.command(name='show', aliases=['display','print'])
    #@commands.is_owner()
    #async def showconf(self, ctx):
    #    """Display Bot configuration""" 
    #    if os.path.isfile(self.config):
    #        with open(self.config, 'r') as file:
    #            settings = json.load(file)
    #        await ctx.send('```json\n' + json.dumps(settings, indent=4) + '\n```')
#
#
    #@conf.command(name='save', aliases=['register'])
    #@commands.is_owner()
    #async def saveconfig(self, ctx):
    #    """Save bot configuration"""
    #    settings = {}
    #    settings['name'] = self.bot.user.name
    #    settings['avatar_url'] = self.bot.user.avatar_url
    #    with open (self.config, 'w') as file:
    #        json.dump(settings, file)
    #    await ctx.send("**`Config succesfully saved.`**")

    @conf.command(name='get', aliases=['retrieve'])
    @commands.is_owner()
    async def getparam(self, ctx, param):
        """Return any bot parameter by its name (https://discordpy.readthedocs.io/en/rewrite/api.html#user)"""
        await ctx.send(str(getattr(self.bot.user, param)))

        # List params
        #dict = {
        #    i: getattr(self.bot.user, i)
        #    for i in dir(self.bot.user)
        #}


    @conf.group(name='set', aliases=['change'])
    @commands.is_owner()
    async def set(self, ctx):
        """Change bot parameters"""

        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid config command passed...')
            return

        log.info(f"{ctx.author} changed {ctx.command.name} parameter to "
                "{ctx.command.parameter}")


    @set.command(name='username', aliases=['nick','pseudo','nickname','name'])
    @commands.is_owner()
    async def username(self, ctx, name):
        """Change bot username"""
        await self.bot.user.edit(username=name)
        

    @set.command(name='avatar', aliases=['image','pic','profilepic'])
    @commands.is_owner()
    async def avatar(self, ctx, url):
        """Change bot avatar"""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                image = await r.read()  
                await self.bot.user.edit(avatar=image)
        

    #
    # ERROR HANDLER
    #
    @getparam.error
    async def getparam_handler(self, ctx, error):
        # Check if our required argument is missing.
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("This parameter doesn't exists!")
        elif isinstance(error, commands.MissingRequiredArgument):
            params_list = [ i for i in dir(self.bot.user) if not i.startswith('_') ]
            embed = discord.Embed(description=f'```{", ".join(params_list)}```')
            await ctx.send("Provide a parameter please sir!", embed=embed)

def setup(bot):
    bot.add_cog(Configs_Commands(bot))

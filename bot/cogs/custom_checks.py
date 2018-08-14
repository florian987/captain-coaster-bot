from discord.ext import commands
import discord


class EventCog:
    def __init__(self, bot):
        self.bot = bot

    def is_not_dm(self, ctx):
        return ctx.guild is None

    async def on_ready(self):
        self.bot.add_check(is_not_dm)

def setup(bot):
    bot.add_cog(EventCog(bot))

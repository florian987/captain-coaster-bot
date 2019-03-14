import asyncio
import logging

from discord.ext import commands

from bot.decorators import in_dm
from bot.utils.embedconverter import build_embed

log = logging.getLogger(__name__)


class Jobs(commands.Cog, name='Jobs Cog'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='jobs', aliases=[])
    @in_dm()
    async def jobs(self, ctx):
        """Create a job embed"""

        await ctx.send(content="Quel job ?")
        try:
            job_msg = await self.bot.wait_for('message', timeout=30)
        except asyncio.TimeoutError:
            pass
        else:
            job = job_msg.content

        await ctx.send(content="Salaire ?")
        try:
            salary_msg = await self.bot.wait_for('message', timeout=30)
        except asyncio.TimeoutError:
            pass
        else:
            salary = salary_msg.content

        await ctx.send(content="Description ?")
        try:
            descr_msg = await self.bot.wait_for('message', timeout=30)
        except asyncio.TimeoutError:
            pass
        else:
            descr = descr_msg.content

        embed = await build_embed(ctx, colour='green', title=job, description=descr, salary=salary)
        await ctx.send(embed=embed)

        # embed doc


def setup(bot):
    bot.add_cog(Jobs(bot))

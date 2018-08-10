from discord.ext import commands
from discord.ext.commands import Context
import discord
import shlex
import random
import re


class Poll_Commands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='poll', aliases=['vote'])
    @commands.guild_only()
    async def poll(self, ctx: Context, *, args: str):
        """Start a poll.
        Usage: /poll "Question ?" "Choice 1" "Choice 2" "Choice 3"
        """

        # Replace mentions
        user_mentions = re.findall(r'(<@!?[0-9]+>)', args)
        for user_mention in user_mentions:
            user_id = re.search(r'<@!?([0-9]+)>', user_mention).group(1)
            print('-' * 200)
            print(user_mention)
            print(user_id)
            print(ctx.guild.get_member(int(user_id)).nick)
            print(args)
            args = args.replace(user_mention, '@' + ctx.guild.get_member(int(user_id)).nick)
            print(args)

        splitted_args = shlex.split(args)

        print(splitted_args)

        if len(splitted_args) < 3:
            return


        embed = discord.Embed(
            title = splitted_args.pop(0)
        )

        used_emojis = []
        allowed_emojis = [e for e in self.bot.emojis if e.guild == ctx.guild and not e.managed]
        
        while len(splitted_args):
            chosen_emoji = random.choice([e for e in allowed_emojis if not e in used_emojis])
            embed.add_field(name=splitted_args.pop(0), value=chosen_emoji, inline=True)
            used_emojis.append(chosen_emoji)

        message = await ctx.send(content='', embed=embed)

        while len(used_emojis):
            await message.add_reaction(used_emojis.pop(0))

    #
    # ERROR HANDLER
    #
    @poll.error
    async def getparam_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Title",
                description="Description",
                colour=ctx.author.color
            )
            await ctx.send(content='', embed=embed)

#Not enough emojis
#Command raised an exception: IndexError: Cannot choose from an empty sequence
#<built-in method with_traceback of CommandInvokeError object at 0x0000020A17030EE8>

def setup(bot):
    bot.add_cog(Poll_Commands(bot))

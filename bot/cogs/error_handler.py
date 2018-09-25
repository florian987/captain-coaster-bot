import sys
import traceback

import discord
from discord.ext import commands

"""
If you are not using this inside a cog, add the event decorator e.g:
@bot.event
async def on_command_error(ctx, error)

For examples of cogs see:
Rewrite:
https://gist.github.com/EvieePy/d78c061a4798ae81be9825468fe146be
Async:
https://gist.github.com/leovoel/46cd89ed6a8f41fd09c5

This example uses @rewrite version of the lib. For the async version of the
lib, simply swap the places of ctx, and error.
e.g: on_command_error(self, error, ctx)

For a list of exceptions:
http://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html#errors
"""


class CommandErrorHandler:
    def __init__(self, bot):
        self.bot = bot

    async def on_command_error(self, ctx, error):
        """
        The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception
        """

        # traceback.print_exception(
        #   type(error), error, error.__traceback__, file=sys.stderr)

        # owner = self.bot.get_user(self.bot.owner_id)
        # self.bot.appinfo = await self.bot.application_info() # Store appinfos
        paginator = commands.Paginator(prefix="```py", suffix="```")

        traceback_msg = "".join(
            traceback.format_exception(
                type(error), error, error.__traceback__
            )
        )

        # Create traceback pages
        for line in traceback_msg.splitlines():
            paginator.add_line(line)

        # Create embed
        embed = discord.Embed(
            title="Fix ya shit",
            colour=discord.Colour.dark_red()
        )

        embed.add_field(name="Requester", value=ctx.author)

        if ctx.guild:
            embed.add_field(
                name="Guild",
                value=ctx.guild
            )
        embed.add_field(
            name="Channel",
            value=f'#{ctx.channel}'
        )
        embed.add_field(
            name="Cog",
            value=f"{ctx.cog}"
        )
        embed.add_field(
            name="Command",
            value=f'```\n{ctx.message.content}\n```'
        )
        embed.add_field(
            name='error',
            value=f"```py\n{error}\n```",
            inline=False
        )
        if hasattr(error, "original"):
            embed.add_field(
                name='original',
                value=f"```py\n{error.original}\n```",
                inline=False
            )

        print('-' * 20)
        print(len(traceback_msg))

        await self.bot.appinfo.owner.send(content="", embed=embed)  # Send error infos

        for page in paginator.pages:  # Send paginated traceback
            await self.bot.appinfo.owner.send(content=page)

        print('-' * 22)
        print(dir(error))
        print(error)
        # print(error.with_traceback())
        print(error.original)
        print('-' * 22)

        # This prevents any commands with local handlers
        # being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.CommandNotFound, commands.UserInputError)

        # Allows us to check for original exceptions raised
        # and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed
        # to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(f'{ctx.command} has been disabled.')

        # Not Working
        # elif isinstance(error, commands.MissingRequiredArgument):
        #    return await ctx.send(f'{ctx.command} need at least 1 argument.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(
                    f'{ctx.command} can not be used in Private Messages.'
                )
            except Exception:
                pass

        # For this error example we check to see where it came from...
        elif isinstance(error, commands.BadArgument):
            # Check if the command being invoked is 'tag list'
            if ctx.command.qualified_name == 'tag list':
                return await ctx.send(
                    'I could not find that member. Please try again.'
                )

        # All other Errors not returned come here...
        # And we can just print the default TraceBack.
        print(
            f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr)


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))

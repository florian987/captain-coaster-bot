from discord.ext import commands
import discord


class Default_Commands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='embed', aliases=['embedtest','testembed','embd','embdtest','testembd'])
    @commands.guild_only()
    async def testembed(self, ctx, title="Title", descr="description"):
        """A simple command which generate embeds.
        Examples:
        /embd "Title" "description"
        """

        # embed doc
        # https://cdn.discordapp.com/attachments/84319995256905728/252292324967710721/embed.png

        embed = discord.Embed(
            title=title,
            description=descr,
            colour=ctx.author.colour)

        embed.set_author(icon_url=ctx.author.avatar_url,
                         name=title,
                         url='https://virtualracingschool.appspot.com/')

        embed.set_image(url='https://d3bxz2vegbjddt.cloudfront.net/members/member_images/series/seriesid_231/logo.jpg')
        
        embed.add_field(name='Track', value='Motegi',inline=True)
        embed.add_field(name='Field1', value='not-inline',inline=False)

        await ctx.send(content='', embed=embed)



def setup(bot):
    bot.add_cog(Default_Commands(bot))

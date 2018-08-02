import discord

def build_embed(**kwargs):

            title = kwargs.pop('title', "Titre")
            descr = kwargs.pop('descr', "Description")
            colour = kwargs.pop('colour', ctx.author.color)
            img = kwargs.pop('img', None)
            author_icon = kwargs.pop('author_icon', ctx.author.avatar_url)
            author_name = kwargs.pop('author_icon', ctx.author.name)
            author_url = kwargs.pop('author_url', ctx.author.avatar_url)
            print_dict = kwargs.pop('print_dict', False)
            footer_text = kwargs.pop('footer_text', None)
            footer_icon = kwargs.pop('footer_icon', None)
            content = ''

            embed = discord.Embed(
                title=title,
                description=descr,
                colour=colour
            )

            embed.set_author(
                icon_url=author_icon,
                name=author_name,
                url=author_url
            )

            if img:
                embed.set_image(url=img)

            if footer_text or footer_icon:
                embed.set_footer(text=footer_text,icon_url=footer_icon)

            for key, value in kwargs.items():
                embed.add_field(name=key, value=value, inline=True)


            if print_dict:
                content = embed.to_dict()

            return content, embed
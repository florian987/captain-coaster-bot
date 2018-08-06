from discord.ext import commands
import discord


def build_embed(ctx, **kwargs):
    """A function that build embeds"""

    # Create embed with basics parameters
    embed = discord.Embed()

    # Set img if set
    embed.title = kwargs.pop('title',  'Awesome Title!')
    embed.description = kwargs.pop('description', 'Description goes here.')
    embed.colour = kwargs.pop('colour', discord.Colour.default())

    embed.set_image(url=kwargs.pop('img_url', discord.Embed.Empty))

    embed.set_author(
        icon_url=kwargs.pop('author_avatar_url', discord.Embed.Empty),
        name=kwargs.pop('author_name', discord.Embed.Empty),
        url=kwargs.pop('author_url', discord.Embed.Empty)
    )

    embed.set_footer(
        text=kwargs.pop('footer_text', discord.Embed.Empty),
        icon_url=kwargs.pop('footer_icon', discord.Embed.Empty)
    )

    # Set remaining args as fields
    if kwargs:
        for k, v in kwargs.items():
            embed.add_field(name=k, value=v, inline=True) 

    return embed
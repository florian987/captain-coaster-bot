import discord


async def build_embed(ctx, **kwargs):
    """
    A simple helper class to help generating embeds.

    https://cdn.discordapp.com/attachments/84319995256905728/252292324967710721/embed.png

    Examples:
    build_embed(titre="Title", descr="Description")
    """

    title = kwargs.pop('title', None)
    descr = kwargs.pop('description', None)
    colour = kwargs.pop('colour', discord.Embed.Empty)
    img = kwargs.pop('img', None)
    author_icon = kwargs.pop('author_icon', discord.Embed.Empty)
    author_name = kwargs.pop('author_name', None)
    author_url = kwargs.pop('author_url', discord.Embed.Empty)
    footer_text = kwargs.pop('footer_text', None)
    footer_icon = kwargs.pop('footer_icon', None)

    embed = discord.Embed()

    if title:
        embed.title = title

    if descr:
        embed.description = descr

    if colour:
        try:
            embed.colour = await discord.ext.commands.ColourConverter().convert(ctx, colour)
        except Exception as e:
            embed.colour = discord.Embed.Empty

    if author_name:
        embed.set_author(
            icon_url=author_icon,
            name=author_name,
            url=author_url
        )

    if img:
        embed.set_image(url=img)

    if footer_text or footer_icon:
        embed.set_footer(text=footer_text, icon_url=footer_icon)

    for key, value in kwargs.items():
        embed.add_field(name=key, value=value, inline=True)

    return embed

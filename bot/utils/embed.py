import discord


def build_embed(**kwargs):
    """
    A simple helper class to help generating embeds.
    https://cdn.discordapp.com/attachments/84319995256905728/252292324967710721/embed.png

    Examples:
    build_embed(titre="Titre", descr="Description")
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

    builtin_colors = {
        "default": discord.Colour.default(),
        "blue": discord.Colour.blue(),
        "blurple": discord.Colour.blurple(),
        "dark_blue": discord.Colour.dark_blue(),
        "dark_gold": discord.Colour.dark_gold(),
        "dark_green": discord.Colour.dark_green(),
        "dark_grey": discord.Colour.dark_grey(),
        "dark_magenta": discord.Colour.dark_magenta(),
        "dark_orange": discord.Colour.dark_orange(),
        "dark_purple": discord.Colour.dark_purple(),
        "dark_red": discord.Colour.dark_red(),
        "dark_teal": discord.Colour.dark_teal(),
        "gold": discord.Colour.gold(),
        "green": discord.Colour.green(),
        "greyple": discord.Colour.greyple(),
        "light_grey": discord.Colour.light_grey(),
        "lighter_grey": discord.Colour.lighter_grey(),
        "magenta": discord.Colour.magenta(),
        "orange": discord.Colour.orange(),
        "purple": discord.Colour.purple(),
        "red": discord.Colour.red(),
        "teal": discord.Colour.teal(),
    }

    embed = discord.Embed()

    if title:
        embed.title = title

    if descr:
        embed.description = descr

    if colour:
        try:
            colour = discord.Color(int(colour))
        except ValueError:
            if colour in builtin_colors:
                colour = builtin_colors.get(colour)
            else:
                colour = discord.Colour.default()
        embed.colour = colour

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

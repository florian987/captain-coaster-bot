from discord.ext import commands
import discord


def build_embed(ctx, **kwargs):

    parameters = {
        'author_avatar_url': ctx.author.avatar_url,
        'author_name': ctx.author.name,
        'author_url': ctx.author.url,
        'colour': discord.Colour.default(),
        'img_url': None,
        'footer_text': None,
        'footer_icon': None,
        'title': 'Title',
        'description': 'Description',
        'content': ''
    }

    for parameter in parameters.items():
        if parameter in kwargs:
            parameters[parameter] = kwargs.pop(parameter)
            
    embed = discord.Embed(
        title = parameters['title'],
        description = parameters['description'],
        colour = parameters['colour']
    )
    
    if kwargs:
        for k, v in kwargs:
            embed.add_field(name=k, value=v, inline=True)


    if icon_url is None:
        icon_url=ctx.author.avatar_url

    embed = discord.Embed(
        title=title,
        description=descr,
        colour=colour
    )

    embed.set_author(
        icon_url=ctx.author.avatar_url,
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
from discord.ext import commands
import discord


def build_embed(ctx, **kwargs):
    """A function that build embeds"""
    
    # Set default parameters
    parameters = {
        'author_avatar_url': ctx.author.avatar_url,
        'author_name': ctx.author.name,
        'author_url': ctx.author.avatar_url,
        'colour': discord.Colour.default(),
        'img_url': None,
        'footer_text': None,
        'footer_icon': None,
        'title': 'Title',
        'description': 'Description',
        'content': ''
    }

    # Replace defaults parameters with args
    for parameter in parameters.items():
        if parameter in kwargs:
            parameters[parameter] = kwargs.pop(parameter)
            

    # Create embed with basics parameters
    embed = discord.Embed(
        title = parameters['title'],
        description = parameters['description'],
        colour = parameters['colour']
    )

    # set author
    if parameters['author_avatar_url'] or parameters['author_name'] or parameters['author_url']:
        embed.set_author(
            icon_url=parameters['author_avatar_url'],
            name=parameters['author_name'],
            url=parameters['author_url']
        )
    
    # Set remaining args as fields
    if kwargs:
        for k, v in kwargs.items():
            embed.add_field(name=k, value=v, inline=True) 

    # Set img if set
    if parameters['img_url']:
        embed.set_image(url=parameters['img_url'])

    # Define footer if set
    if parameters['footer_text'] or parameters['footer_icon']:
        embed.set_footer(
            text=parameters['footer_text'], icon_url=parameters['footer_icon']
        )

    return parameters['content'], embed
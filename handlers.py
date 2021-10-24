import functools
import logging

import common
import discord

async def handle_notifications(message, *, sometimes_role, always_role, channel_role, pings_channel):
    """Handler for notifications that the bot must deliver."""
    if not common.has_url(message.content):
        return

    embed = discord.Embed(title='A game is being hosted!', description=message.content)
    embed.add_field(name='Host', value=message.author.name)

    guild = message.guild
    channel_role = guild.get_role(channel_role)
    always_role = guild.get_role(always_role)
    sometimes_role = guild.get_role(sometimes_role)
    pings_channel = guild.get_channel(pings_channel)

    for member in guild.members:
        try:
            if member.bot:
                continue

            if always_role in member.roles:
                pass
            elif sometimes_role in member.roles:
                if member.status == discord.Status.offline:
                    continue
            else:
                continue

            # Send message via user's preferred method
            if channel_role in member.roles:
                await pings_channel.send(member.mention, embed=embed)
            else:
                await common.send_dm_embed(embed, member)
        except Exception as e:
            logging.error(e)

async def handle_suggestions(message):
    """Handler for messages sent in the suggestions channel."""
    await message.add_reaction('👍')
    await message.add_reaction('👎')

async def handle_mentions(message):
    """Handler for messages sent in the suggestions channel."""
    await message.add_reaction('🤍')

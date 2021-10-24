import extra
import discord

import logging

async def handle_dm(bot, message, reports_channel_id):
    """Handler for direct messages received by the bot."""
    if message.author != bot.user:
        channel = bot.get_channel(reports_channel_id)
        embed = discord.Embed(title='Report', description=message.content)
        await channel.send(embed=embed)
        await message.add_reaction('👍')

async def handle_notifications(message, *, sometimes_role, always_role, channel_role, pings_channel):
    """Handler for notifications that the bot must deliver."""
    if not extra.has_url(message.content):
        return

    embed = discord.Embed(title='A game is being hosted!', description=message.content)
    embed.add_field(name="Host", value=message.author.name)

    channel = message.channel
    guild = channel.guild
    channel_role = guild.get_role(channel_role)
    pings_channel = guild.get_channel(pings_channel)

    for member in message.guild.members:
        try:
            if member.bot:
                continue

            roles = member.roles
            # Don't notify offline users
            if message.guild.get_role(sometimes_role) in roles:
                if member.status == discord.Status.offline:
                    continue
            elif message.guild.get_role(always_role) in roles:
                pass

            # Send message via user's preferred method
            if channel_role in member.roles:
                await pings_channel.send(member.mention, embed=embed)
            else:
                await extra.send_dm_embed(embed, member)
        except Exception as e:
            logging.error(e)

async def handle_suggestions(message):
    """Handler for messages sent in the suggestions channel."""
    await message.add_reaction('👍')
    await message.add_reaction('👎')

async def handle_mentions(message):
    """Handler for messages sent in the suggestions channel."""
    await message.add_reaction('🤍')
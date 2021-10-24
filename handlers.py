import extra
import discord

async def handle_dm(bot, message, reports_channel_id):
    """Handler for direct messages received by the bot."""
    if message.author != bot.user:
        channel = bot.get_channel(reports_channel_id)
        embed = discord.Embed(title='Report', description=message.content)
        await channel.send(embed=embed)
        await message.add_reaction('👍')

async def handle_notifications(message, *, sometimes_role, always_role):
    """Handler for notifications that the bot must deliver."""
    if not extra.has_url(message.content):
        return

    for member in message.guild.members:
        try:
            roles = member.roles
            # Don't notify offline users
            if message.guild.get_role(sometimes_role) in roles:
                if member.status == discord.Status.offline:
                    continue
            elif message.guild.get_role(always_role) in roles:
                pass

            # Format message
            embed = discord.Embed(title='A game is being hosted!', description=message.content)
            embed.add_field(name="Host", value=message.author.name)

            await extra.send_dm_embed(embed, member)
        except:
            pass

async def handle_suggestions(message):
    """Handler for messages sent in the suggestions channel."""
    await message.add_reaction('👍')
    await message.add_reaction('👎')

async def handle_mentions(message):
    """Handler for messages sent in the suggestions channel."""
    await message.add_reaction('🤍')
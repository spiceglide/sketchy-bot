import common

import logging

import discord
from discord.ext import commands

logging.basicConfig(filename='log.txt', level=logging.INFO)

class Admin(commands.Cog):
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *reason):
        reason = ' '.join(reason)
        embed = common.create_embed({
            'title': 'Ban',
            'description': f'{member.name} has been banned.',
            'Reason': reason,
        })

        await common.send_dm_embed(embed, member)
        await ctx.send(embed=embed)
        await member.ban(reason=reason)
        logging.info(f'Member {member} banned')

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *reason):
        reason = ' '.join(reason)
        embed = common.create_embed({
            'title': 'Kick',
            'description': f'{member.name} has been kicked.',
            'Reason': reason,
        })

        await common.send_dm_embed(embed, member)
        await ctx.send(embed=embed)
        await member.kick(reason=reason)
        logging.info(f'Member {member} kicked')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member):
        await ctx.send('Sorry! Muting is not implemented yet')

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *reason):
        reason = ' '.join(reason)
        embed = common.create_embed({
            'title': 'Warning',
            'description': f'{member.name} has been warned.',
            'Reason': reason,
        })

        await common.send_dm_embed(embed, member)
        await ctx.send(embed=embed)
        logging.info(f'Member {member} warned')

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def approve(self, ctx, member: discord.Member):
        verified_role = ctx.guild.get_role(self.settings['roles']['verified'])
        notify_role = ctx.guild.get_role(self.settings['roles']['sometimes_ping'])

        if member.bot:
            await member.add_roles(bot_role)
        else:
            await member.add_roles(verified_role, notify_role)

        await ctx.message.add_reaction('👍')
        logging.info(f'Member {member} approved')

    #@commands.has_permissions(manage_messages=True)
    @commands.command()
    async def puppet(self, ctx, channel, *message):
        message = ' '.join(message)
        guild = self.bot.get_guild(self.settings['guild'])

        if channel.isdigit():
            channel = guild.get_channel(int(channel))
        else:
            channel = channel.lstrip('#')
            channel = [chnl for chnl in guild.text_channels if chnl.name == channel][0]

        await channel.send(message)
        await ctx.message.add_reaction('👍')
        logging.info('Puppetting handled')

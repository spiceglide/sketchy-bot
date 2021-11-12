import common
import handlers
import database

import logging
from copy import copy

import discord
from discord.ext import commands

logging.basicConfig(filename='log.txt', level=logging.INFO)

class Regular(commands.Cog):
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return

        # A welcoming message
        embed = discord.Embed(title='Welcome to Sketchspace!', description='A community for playing art games')
        await common.send_dm_embed(embed, member)

        database.add_member(member, self.settings['paths']['database'])
        logging.info(f'Member {member} joined')

    @commands.Cog.listener()
    async def on_message(self, message):
        # Game notifications
        if message.channel == self.bot.get_channel(self.settings['channels']['games']):
            await handlers.handle_notifications(
                message,
                sometimes_role=self.settings['roles']['sometimes_ping'],
                always_role=self.settings['roles']['always_ping'],
                channel_role=self.settings['roles']['channel_ping'],
                pings_channel=self.settings['channels']['pings'],
            )
            logging.info('Notification handled')
        # Suggestions
        elif message.channel == self.bot.get_channel(self.settings['channels']['suggestions']):
            await handlers.handle_suggestions(message)
            logging.info('Suggestion handled')
            return
        # Mentions
        elif self.bot.user.mentioned_in(message):
            await handlers.handle_mentions(message)
            logging.info('Mention handled')

        # Process any commands
        await self.bot.process_commands(message)

    @commands.command()
    async def role(self, ctx, color, *name):
        """Set the name and colour of your own role."""
        name = ' '.join(name)
        color = common.hex_to_color(color)

        with database.db(self.settings['paths']['database']) as cursor:
            role_assigned = cursor.execute('SELECT role FROM members WHERE id = ?', (ctx.author.id,)).fetchone()
            # If no assigned role, create a new one
            if role_assigned[0] == None:
                role = await ctx.guild.create_role(name=name, color=color)
                old_role = None
                new_role = role

                # Set role position above the generic roles
                boundary_role = ctx.guild.get_role(self.settings['roles']['custom_boundary'])
                role_position = boundary_role.position + 1
                await role.edit(position=role_position)

                # Add to user and database
                await ctx.author.add_roles(role)
                cursor.execute('INSERT INTO roles(id) VALUES(?)', (role.id,))
                cursor.execute('UPDATE members SET role = ? WHERE id = ?', (role.id, ctx.author.id))
            else:
                role = ctx.guild.get_role(role_assigned[0])
                old_role = copy(role)

                if name == '':
                    await role.edit(color=color)
                else:
                    await role.edit(name=name, color=color)
                new_role = role

        summary = common.compare_roles(old_role, new_role)
        embed = common.create_embed({
            'title': 'Role update',
            'Name': summary['name'],
            'Color': summary['color'],
        }, inline=False, color=color)
        await ctx.send(embed=embed)

        logging.info(f'Role for member {ctx.author} updated')

    @commands.command()
    async def suggest(self, ctx, *message):
        """Anonymously post a suggestion."""
        message = ' '.join(message)
        channel = self.bot.get_channel(self.settings['channels']['suggestions'])

        await channel.send(message)
        await ctx.message.add_reaction('👍')
        logging.info('Suggestion handled')

    @commands.command()
    async def report(self, ctx, *message):
        """Anonymously report a member."""
        message = ' '.join(message)
        channel = self.bot.get_channel(self.settings['channels']['reports'])
        embed = discord.Embed(title='Report', description=message)

        await channel.send(embed=embed)
        await ctx.message.add_reaction('👍')
        logging.info('Report handled')
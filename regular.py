import common
from sqlite_context_manager import db

import logging
from copy import copy

import discord
from discord.ext import commands

logging.basicConfig(filename='log.txt', level=logging.INFO)

class Regular(commands.Cog):
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

    @commands.command()
    async def role(self, ctx, color, *name):
        name = ' '.join(name)
        color = common.hex_to_color(color)

        with db(self.settings['paths']['database']) as cursor:
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
        message = ' '.join(message)
        channel = self.bot.get_channel(self.settings['channels']['suggestions'])

        await channel.send(message)
        await ctx.message.add_reaction('👍')
        logging.info('Suggestion handled')

    @commands.command()
    async def report(self, ctx, *message):
        message = ' '.join(message)
        channel = self.bot.get_channel(self.settings['channels']['reports'])
        embed = discord.Embed(title='Report', description=message)

        await channel.send(embed=embed)
        await ctx.message.add_reaction('👍')
        logging.info('Report handled')
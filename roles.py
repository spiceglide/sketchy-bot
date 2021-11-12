import common
from database import db

import logging

import discord
from discord.ext import commands

logging.basicConfig(filename='log.txt', level=logging.INFO)

class Roles(commands.Cog):
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.autoroles = common.read_json(settings['paths']['autoroles'])['autoroles']

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        with database.db(self.settings['paths']['database']) as cursor:
            role_is_relevant = cursor.execute('SELECT EXISTS(SELECT id FROM roles WHERE id = ?)', (role.id,)).fetchone()
            if role_is_relevant[0] != 0:
                cursor.execute('DELETE FROM roles WHERE id = ?', (role.id,))
                cursor.execute('UPDATE members SET role = NULL WHERE role = ?', (role.id,))
        logging.info(f'Role {role} deleted')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id != self.settings['channels']['roles']:
            return
        if self.settings['setup']['autoroles']:
            return

        guild = self.bot.get_guild(self.settings['guild'])
        data = common.get_autorole_data(payload.message_id, self.autoroles)
        role = common.get_autorole_role_from_reaction(payload.emoji.name, data, guild)
        await payload.member.add_roles(role)
        logging.info(f'Role {role} added to member {payload.member}')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.channel_id != self.settings['channels']['roles']:
            return
        if self.settings['setup']['autoroles']:
            return

        guild = self.bot.get_guild(self.settings['guild'])
        data = common.get_autorole_data(payload.message_id, self.autoroles)
        role = common.get_autorole_role_from_reaction(payload.emoji.name, data, guild)

        member = guild.get_member(payload.user_id)
        await member.remove_roles(role)
        logging.info(f'Role {role} removed from member {member}')
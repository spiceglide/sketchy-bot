#!/usr/bin/env python3

import common
import handlers
from sqlite_context_manager import db

from admin import Admin
from regular import Regular
from music import Music

import json
import logging
import os
from copy import copy
from sys import exit

import sqlite3
import discord
from discord.ext import commands

SETTINGS = common.read_json('config.json')
AUTOROLES = common.read_json(SETTINGS['paths']['autoroles'])['autoroles']

logging.basicConfig(filename='log.txt', level=logging.INFO)
common.setup_db(SETTINGS['paths']['database'])

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.presences = True
intents.reactions = True

bot = commands.Bot(command_prefix=SETTINGS['prefix'], intents=intents)

@bot.event
async def on_ready():
    guild = bot.get_guild(SETTINGS['guild'])
    logging.info(
        'Connection established\n'
        f'User name:  {bot.user.name}\n'
        f'User ID:    {bot.user.id}\n'
        f'Guild name: {guild.name}\n'
        f'Guild ID:   {guild.id}\n'
    )

    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(type=discord.ActivityType.watching, name='the stars'),
    )

    members = bot.get_all_members()
    common.update_members_db(members, SETTINGS['paths']['database'])

    # Create auto-role messages
    if SETTINGS['setup']['autoroles']:
        for autorole in AUTOROLES:
            if autorole['message'] != 0:
                continue

            embed = discord.Embed(title=autorole['title'])

            for emoji, description in zip(autorole['reactions'], autorole['descriptions']):
                embed.add_field(name=emoji, value=description)

            channel = bot.get_channel(SETTINGS['channels']['roles'])
            message = await channel.send(embed=embed)

            for emoji in autorole['reactions']:
                await message.add_reaction(emoji)

        logging.info('Auto-roles set up!')
        logging.info('Please set the message IDs in the autoroles.json file and disable the SKETCHY_SETUP_AUTOROLES flag before restarting')
        exit()

@bot.event
async def on_member_join(member):
    if member.bot:
        return

    # A welcoming message
    embed = discord.Embed(title='Welcome to Sketchspace!', description='A community for playing art games')
    await common.send_dm_embed(embed, member)

    common.add_member_db(member, SETTINGS['paths']['database'])
    logging.info(f'Member {member} joined')

@bot.event
async def on_message(message):
    # Game notifications
    if message.channel == bot.get_channel(SETTINGS['channels']['games']):
        await handlers.handle_notifications(
            message,
            sometimes_role=SETTINGS['roles']['sometimes_ping'],
            always_role=SETTINGS['roles']['always_ping'],
            channel_role=SETTINGS['roles']['channel_ping'],
            pings_channel=SETTINGS['channels']['pings'],
        )
        logging.info('Notification handled')
    # Suggestions
    elif message.channel == bot.get_channel(SETTINGS['channels']['suggestions']):
        await handlers.handle_suggestions(message)
        logging.info('Suggestion handled')
        return
    # Mentions
    elif bot.user.mentioned_in(message):
        await handlers.handle_mentions(message)
        logging.info('Mention handled')

    # Process any commands
    await bot.process_commands(message)

@bot.event
async def on_guild_role_delete(role):
    with db(SETTINGS['paths']['database']) as cursor:
        role_is_relevant = cursor.execute('SELECT EXISTS(SELECT id FROM roles WHERE id = ?)', (role.id,)).fetchone()
        if role_is_relevant[0] != 0:
            cursor.execute('DELETE FROM roles WHERE id = ?', (role.id,))
            cursor.execute('UPDATE members SET role = NULL WHERE role = ?', (role.id,))
    logging.info(f'Role {role} deleted')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id != SETTINGS['channels']['roles']:
        return
    if SETTINGS['setup']['autoroles']:
        return

    guild = bot.get_guild(SETTINGS['guild'])
    data = common.get_autorole_data(payload.message_id, AUTOROLES)
    role = common.get_autorole_role_from_reaction(payload.emoji.name, data, guild)
    await payload.member.add_roles(role)
    logging.info(f'Role {role} added to member {payload.member}')

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id != SETTINGS['channels']['roles']:
        return
    if SETTINGS['setup']['autoroles']:
        return

    guild = bot.get_guild(SETTINGS['guild'])
    data = common.get_autorole_data(payload.message_id, AUTOROLES)
    role = common.get_autorole_role_from_reaction(payload.emoji.name, data, guild)

    member = guild.get_member(payload.user_id)
    await member.remove_roles(role)
    logging.info(f'Role {role} removed from member {member}')

bot.add_cog(Admin(bot, SETTINGS))
bot.add_cog(Regular(bot, SETTINGS))
bot.add_cog(Music(bot, SETTINGS))
bot.run(SETTINGS['token'])
#!/usr/bin/env python3

import common
import handlers
import database

from admin import Admin
from regular import Regular
from roles import Roles
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
database.setup(SETTINGS['paths']['database'])

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

    members = bot.get_all_members()
    database.update_members(members, SETTINGS['paths']['database'])

bot.add_cog(Admin(bot, SETTINGS))
bot.add_cog(Regular(bot, SETTINGS))
bot.add_cog(Roles(bot, SETTINGS))
bot.add_cog(Music(bot, SETTINGS))
bot.run(SETTINGS['token'])
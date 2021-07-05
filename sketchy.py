#!/usr/bin/env python3

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('SKETCHY_TOKEN')
GUILD = int(os.getenv('SKETCHY_GUILD'))
PREFIX = os.getenv('SKETCHY_PREFIX')

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    guild = bot.get_guild(GUILD)
    print(
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

@bot.event
async def on_member_join(member):
    # Unverify newbies
    guild = bot.get_guild(GUILD)
    role = guild.get_role(UNVERIFIED_ROLE)
    await member.add_roles(role)

    # A welcoming message
    dm = await member.create_dm()
    await dm.send('Welcome to Sketchspace!')

@bot.command()
async def ban(ctx):
    await ctx.send('Sorry! Banning is not implemented yet')

@bot.command()
async def kick(ctx):
    await ctx.send('Sorry! Kicking is not implemented yet')

@bot.command()
async def mute(ctx):
    await ctx.send('Sorry! Muting is not implemented yet')

bot.run(TOKEN)

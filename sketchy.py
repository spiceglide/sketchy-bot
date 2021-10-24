#!/usr/bin/env python3

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import sqlite3

load_dotenv()

# Set up the database if it doesn't already exist
if not os.path.exists('data.db'):
    connection = sqlite3.connect('data.db')
    cursor = connection.cursor()

    # TODO: Implement role-setting features using the database
    cursor.execute('''CREATE TABLE roles
                      (id INTEGER PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE members
                      (id INTEGER PRIMARY KEY,
                       role INTEGER,
                       FOREIGN KEY(role) REFERENCES roles(id))''')

    connection.commit()
    connection.close()
    print('Set up database!')

TOKEN = os.getenv('SKETCHY_TOKEN')
GUILD = int(os.getenv('SKETCHY_GUILD'))
PREFIX = os.getenv('SKETCHY_PREFIX')
GAMES_CHANNEL = int(os.getenv('SKETCHY_GAMES_CHANNEL'))
REPORTS_CHANNEL = int(os.getenv('SKETCHY_REPORTS_CHANNEL'))
SUGGESTIONS_CHANNEL = int(os.getenv('SKETCHY_SUGGESTIONS_CHANNEL'))
UNVERIFIED_ROLE = int(os.getenv('SKETCHY_UNVERIFIED_ROLE'))
ALWAYS_PING_ROLE = int(os.getenv('SKETCHY_ALWAYS_PING_ROLE'))
SOMETIMES_PING_ROLE = int(os.getenv('SKETCHY_SOMETIMES_PING_ROLE'))

intents = discord.Intents.default()
intents.members = True
intents.presences = True

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

    connection = sqlite3.connect('data.db')
    cursor = connection.cursor()

    # Make sure database is up-to-date
    for member in bot.get_all_members():
        member_exists = cursor.execute('SELECT EXISTS(SELECT id FROM members WHERE id = ?)', (member.id,)).fetchone()
        if member_exists[0] == 0:
            cursor.execute('INSERT INTO members(id) VALUES(?)', (member.id,))
    
    connection.commit()
    connection.close()
    print('Database updated!', end='\n')

@bot.event
async def on_member_join(member):
    # Unverify newbies
    guild = bot.get_guild(GUILD)
    role = guild.get_role(UNVERIFIED_ROLE)
    await member.add_roles(role)

    # A welcoming message
    embed = discord.Embed(title='Welcome to Sketchspace!', description='A community for playing art games')
    dm = await member.create_dm()
    await dm.send(embed=embed)

@bot.event
async def on_message(message):
    # Direct messages
    if not message.guild:
        if message.author != bot.user:
            channel = bot.get_channel(REPORTS_CHANNEL)
            embed = discord.Embed(title='Report', description=message.content)
            await channel.send(embed=embed)
            await message.add_reaction('👍')
    # Game notifications
    elif message.channel == bot.get_channel(GAMES_CHANNEL):
        for member in message.guild.members:
            # Don't notify bots
            if member.bot:
                continue

            roles = member.roles
            # Don't notify offline users
            if message.guild.get_role(SOMETIMES_PING_ROLE) in roles:
                if member.status == discord.Status.offline:
                    continue
            elif message.guild.get_role(ALWAYS_PING_ROLE) in roles:
                pass

            # Format message
            embed = discord.Embed(title='A game is being hosted!', description=message.content)
            embed.add_field(name="Host", value=message.author.name)

            # Send
            dm = await member.create_dm()
            await dm.send(embed=embed)
    # Suggestions
    elif message.channel == bot.get_channel(SUGGESTIONS_CHANNEL):
        await message.add_reaction('👍')
        await message.add_reaction('👎')
    # Mentions
    elif bot.user.mentioned_in(message):
        await message.add_reaction('🤍')

    # Process any commands
    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member):
    await member.ban()
    embed = discord.Embed(title='Ban', description=f'{member.name} has been banned.')
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member):
    await member.kick()
    embed = discord.Embed(title='Kick', description=f'{member.name} has been kicked.')
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member):
    await ctx.send('Sorry! Muting is not implemented yet')

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member):
    embed = discord.Embed(title='Warning', description=f'{member.name} has been warned.')
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def approve(ctx, member: discord.Member):
    guild = bot.get_guild(GUILD)
    unverified_role = guild.get_role(UNVERIFIED_ROLE)
    notify_role = guild.get_role(SOMETIMES_PING_ROLE)

    await member.remove_roles(unverified_role)
    await member.add_roles(notify_role)
    await ctx.message.add_reaction('👍')

bot.run(TOKEN)
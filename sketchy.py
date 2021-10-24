#!/usr/bin/env python3

import os
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv
import sqlite3

load_dotenv()

# Import settings
TOKEN = os.getenv('SKETCHY_TOKEN')
GUILD = int(os.getenv('SKETCHY_GUILD'))
DATABASE_PATH = os.getenv('SKETCHY_DATABASE_PATH')
PREFIX = os.getenv('SKETCHY_PREFIX')
GAMES_CHANNEL = int(os.getenv('SKETCHY_GAMES_CHANNEL'))
REPORTS_CHANNEL = int(os.getenv('SKETCHY_REPORTS_CHANNEL'))
SUGGESTIONS_CHANNEL = int(os.getenv('SKETCHY_SUGGESTIONS_CHANNEL'))
UNVERIFIED_ROLE = int(os.getenv('SKETCHY_UNVERIFIED_ROLE'))
ALWAYS_PING_ROLE = int(os.getenv('SKETCHY_ALWAYS_PING_ROLE'))
SOMETIMES_PING_ROLE = int(os.getenv('SKETCHY_SOMETIMES_PING_ROLE'))
CUSTOM_BOUNDARY_ROLE = int(os.getenv('SKETCHY_CUSTOM_BOUNDARY_ROLE'))

# Set up the database if it doesn't already exist
if not os.path.exists(DATABASE_PATH):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.execute('''CREATE TABLE roles
                      (id INTEGER PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE members
                      (id INTEGER PRIMARY KEY,
                       role INTEGER,
                       FOREIGN KEY(role) REFERENCES roles(id) ON DELETE SET NULL)''')

    connection.commit()
    connection.close()
    print('Set up database!')

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.guilds = True

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

    connection = sqlite3.connect(DATABASE_PATH)
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
    if not member.bot:
        # Unverify newbies
        guild = bot.get_guild(GUILD)
        role = guild.get_role(UNVERIFIED_ROLE)
        await member.add_roles(role)

        # A welcoming message
        embed = discord.Embed(title='Welcome to Sketchspace!', description='A community for playing art games')
        dm = await member.create_dm()
        await dm.send(embed=embed)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute('INSERT INTO members(id) VALUES(?)', (member.id,))

    connection.commit()
    connection.close()

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
        # Check that the message contains a link
        link_expression = re.compile(r'https?://[a-z0-9\.]+\.[a-z0-9]')
        if link_expression.match(message.content.lower()) == None:
            return

        for member in message.guild.members:
            try:
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
            except:
                pass
    # Suggestions
    elif message.channel == bot.get_channel(SUGGESTIONS_CHANNEL):
        await message.add_reaction('👍')
        await message.add_reaction('👎')
    # Mentions
    elif bot.user.mentioned_in(message):
        await message.add_reaction('🤍')

    # Process any commands
    await bot.process_commands(message)

@bot.event
async def on_guild_role_delete(role):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    role_is_relevant = cursor.execute('SELECT EXISTS(SELECT id FROM roles WHERE id = ?)', (role.id,)).fetchone()
    if role_is_relevant[0] != 0:
        cursor.execute('DELETE FROM roles WHERE id = ?', (role.id,))
        cursor.execute('UPDATE members SET role = NULL WHERE role = ?', (role.id,))

    connection.commit()
    connection.close()

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *reason):
    reason = ' '.join(reason)

    await member.ban(reason=reason)
    embed = discord.Embed(title='Ban', description=f'{member.name} has been banned.')
    embed.add_field(name='Reason', value=reason)
    await ctx.send(embed=embed)

    dm = await member.create_dm()
    await dm.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *reason):
    reason = ' '.join(reason)

    await member.kick(reason=reason)
    embed = discord.Embed(title='Kick', description=f'{member.name} has been kicked.')
    embed.add_field(name='Reason', value=reason)
    await ctx.send(embed=embed)

    dm = await member.create_dm()
    await dm.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member):
    await ctx.send('Sorry! Muting is not implemented yet')

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *reason):
    reason = ' '.join(reason)

    embed = discord.Embed(title='Warning', description=f'{member.name} has been warned.')
    embed.add_field(name='Reason', value=reason)
    await ctx.send(embed=embed)

    dm = await member.create_dm()
    await dm.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def approve(ctx, member: discord.Member):
    guild = bot.get_guild(GUILD)
    unverified_role = guild.get_role(UNVERIFIED_ROLE)
    notify_role = guild.get_role(SOMETIMES_PING_ROLE)

    await member.remove_roles(unverified_role)
    await member.add_roles(notify_role)
    await ctx.message.add_reaction('👍')

@bot.command()
async def role(ctx, color, *name):
    name = ' '.join(name)
    red, green, blue = bytes.fromhex(color.lstrip('#'))
    color = discord.Color.from_rgb(red, green, blue)
    guild = bot.get_guild(GUILD)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    role_assigned = cursor.execute('SELECT role FROM members WHERE id = ?', (ctx.author.id,)).fetchone()
    # If no assigned role, create a new one
    if role_assigned[0] == None:
        role = await guild.create_role(name=name, color=color)

        # Set role position above the generic roles
        boundary_role = guild.get_role(CUSTOM_BOUNDARY_ROLE)
        role_position = boundary_role.position + 1
        await role.edit(position=role_position)

        # Add to user and database
        await ctx.author.add_roles(role)
        cursor.execute('INSERT INTO roles(id) VALUES(?)', (role.id,))
        cursor.execute('UPDATE members SET role = ? WHERE id = ?', (role.id, ctx.author.id))

        name_message = role.name
        color_message = str(role.color)
    else:
        role = guild.get_role(role_assigned[0])
        name_message = role.name
        color_message = str(role.color)

        if name == '':
            await role.edit(color=color)
            color_message += f' → {str(role.color)}'
        else:
            await role.edit(name=name, color=color)
            name_message += f' → {role.name}'
            color_message += f' → {str(role.color)}'

    embed = discord.Embed(title='Role update')
    embed.add_field(name="Name", value=name_message, inline=False)
    embed.add_field(name="Color", value=color_message, inline=False)
    await ctx.send(embed=embed)

    connection.commit()
    connection.close()

bot.run(TOKEN)
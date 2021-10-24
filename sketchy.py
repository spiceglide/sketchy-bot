#!/usr/bin/env python3

import extra
import handlers

import json
import os
import re
from copy import copy
from sys import exit

import sqlite3
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# Import settings
TOKEN = os.getenv('SKETCHY_TOKEN')
GUILD = int(os.getenv('SKETCHY_GUILD'))
DATABASE_PATH = os.getenv('SKETCHY_DATABASE_PATH')
AUTOROLES_PATH = os.getenv('SKETCHY_AUTOROLES_PATH')
PREFIX = os.getenv('SKETCHY_PREFIX')
SETUP_AUTOROLES = int(os.getenv('SKETCHY_SETUP_AUTOROLES'))
GAMES_CHANNEL = int(os.getenv('SKETCHY_GAMES_CHANNEL'))
PINGS_CHANNEL = int(os.getenv('SKETCHY_PINGS_CHANNEL'))
REPORTS_CHANNEL = int(os.getenv('SKETCHY_REPORTS_CHANNEL'))
ROLES_CHANNEL = int(os.getenv('SKETCHY_ROLES_CHANNEL'))
SUGGESTIONS_CHANNEL = int(os.getenv('SKETCHY_SUGGESTIONS_CHANNEL'))
VERIFIED_ROLE = int(os.getenv('SKETCHY_VERIFIED_ROLE'))
ALWAYS_PING_ROLE = int(os.getenv('SKETCHY_ALWAYS_PING_ROLE'))
SOMETIMES_PING_ROLE = int(os.getenv('SKETCHY_SOMETIMES_PING_ROLE'))
CHANNEL_PING_ROLE = int(os.getenv('SKETCHY_CHANNEL_PING_ROLE'))
CUSTOM_BOUNDARY_ROLE = int(os.getenv('SKETCHY_CUSTOM_BOUNDARY_ROLE'))

extra.setup_db(DATABASE_PATH)
AUTOROLES = extra.read_json(AUTOROLES_PATH)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.presences = True
intents.reactions = True

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

    members = bot.get_all_members()
    extra.update_members_db(members, DATABASE_PATH)

    # Create auto-role messages
    if SETUP_AUTOROLES == 1:
        for autorole in AUTOROLES:
            if autorole['message'] != 0:
                continue

            embed = discord.Embed(title=autorole['title'])

            for emoji, description in zip(autorole['reactions'], autorole['descriptions']):
                embed.add_field(name=emoji, value=description)

            channel = bot.get_channel(ROLES_CHANNEL)
            message = await channel.send(embed=embed)

            for emoji in autorole['reactions']:
                await message.add_reaction(emoji)

        print('Auto-roles set up!')
        print('Please set the message IDs in the autoroles.json file and disable the SKETCHY_SETUP_AUTOROLES flag before restarting')
        exit()

@bot.event
async def on_member_join(member):
    if member.bot:
        return

    # A welcoming message
    embed = discord.Embed(title='Welcome to Sketchspace!', description='A community for playing art games')
    await extra.send_dm_embed(embed, member)

    extra.add_member_db(member, DATABASE_PATH)

@bot.event
async def on_message(message):
    # Direct messages
    if not message.guild:
        await handlers.handle_dm(bot, message, REPORTS_CHANNEL)
    # Game notifications
    elif message.channel == bot.get_channel(GAMES_CHANNEL):
        await handlers.handle_notifications(
            message,
            sometimes_role=SOMETIMES_PING_ROLE,
            always_role=ALWAYS_PING_ROLE,
            channel_role=CHANNEL_PING_ROLE,
            pings_channel=PINGS_CHANNEL,
        )
    # Suggestions
    elif message.channel == bot.get_channel(SUGGESTIONS_CHANNEL):
        await handlers.handle_suggestions(message)
        return
    # Mentions
    elif bot.user.mentioned_in(message):
        await handlers.handle_mentions(message)

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

@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id != ROLES_CHANNEL:
        return
    if SETUP_AUTOROLES == 1:
        return

    for autorole in AUTOROLES:
        if payload.message_id == autorole['message']:
            data = autorole
            break

    for emoji, role in zip(data['reactions'], data['roles']):
        if payload.emoji.name == emoji:
            guild = bot.get_guild(GUILD)
            selected_role = guild.get_role(role)
            await payload.member.add_roles(selected_role)
            break

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id != ROLES_CHANNEL:
        return
    if SETUP_AUTOROLES == 1:
        return

    for autorole in AUTOROLES:
        if payload.message_id == autorole['message']:
            data = autorole

    for emoji, role in zip(data['reactions'], data['roles']):
        if payload.emoji.name == emoji:
            guild = bot.get_guild(GUILD)
            selected_role = guild.get_role(role)
            member = guild.get_member(payload.user_id)
            await member.remove_roles(selected_role)
            break

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *reason):
    reason = ' '.join(reason)
    embed = discord.Embed(title='Ban', description=f'{member.name} has been banned.')
    embed.add_field(name='Reason', value=reason)

    await extra.send_dm_embed(embed, member)
    await ctx.send(embed=embed)
    await member.ban(reason=reason)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *reason):
    reason = ' '.join(reason)
    embed = discord.Embed(title='Kick', description=f'{member.name} has been kicked.')
    embed.add_field(name='Reason', value=reason)

    await extra.send_dm_embed(embed, member)
    await ctx.send(embed=embed)
    await member.kick(reason=reason)

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

    await extra.send_dm_embed(embed, member)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def approve(ctx, member: discord.Member):
    verified_role = ctx.guild.get_role(VERIFIED_ROLE)
    notify_role = ctx.guild.get_role(SOMETIMES_PING_ROLE)

    await member.add_roles(verified_role, notify_role)
    await ctx.message.add_reaction('👍')

@bot.command()
async def role(ctx, color, *name):
    name = ' '.join(name)
    red, green, blue = bytes.fromhex(color.lstrip('#'))
    color = discord.Color.from_rgb(red, green, blue)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    role_assigned = cursor.execute('SELECT role FROM members WHERE id = ?', (ctx.author.id,)).fetchone()
    # If no assigned role, create a new one
    if role_assigned[0] == None:
        role = await ctx.guild.create_role(name=name, color=color)

        old_role = None
        new_role = role

        # Set role position above the generic roles
        boundary_role = ctx.guild.get_role(CUSTOM_BOUNDARY_ROLE)
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

    summary = extra.compare_roles(old_role, new_role)

    embed = discord.Embed(title='Role update')
    embed.add_field(name="Name", value=summary['name'], inline=False)
    embed.add_field(name="Color", value=summary['color'], inline=False)
    await ctx.send(embed=embed)

    connection.commit()
    connection.close()

bot.run(TOKEN)
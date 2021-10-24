#!/usr/bin/env python3

import extra
import handlers
from sqlite_context_manager import db

import json
import logging
import os
from copy import copy
from sys import exit

import sqlite3
import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO)
SETTINGS = extra.import_settings()
extra.setup_db(SETTINGS['database_path'])
AUTOROLES = extra.read_json(SETTINGS['autoroles_path'])

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
    extra.update_members_db(members, SETTINGS['database_path'])

    # Create auto-role messages
    if SETTINGS['setup_autoroles'] == 1:
        for autorole in AUTOROLES:
            if autorole['message'] != 0:
                continue

            embed = discord.Embed(title=autorole['title'])

            for emoji, description in zip(autorole['reactions'], autorole['descriptions']):
                embed.add_field(name=emoji, value=description)

            channel = bot.get_channel(SETTINGS['roles_channel'])
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
    await extra.send_dm_embed(embed, member)

    extra.add_member_db(member, SETTINGS['database_path'])
    logging.info(f'Member {member} joined')

@bot.event
async def on_message(message):
    # Direct messages
    if not message.guild:
        await handlers.handle_dm(bot, message, SETTINGS['reports_channel'])
        logging.info('DM handled')
    # Game notifications
    elif message.channel == bot.get_channel(SETTINGS['games_channel']):
        await handlers.handle_notifications(
            message,
            sometimes_role=SETTINGS['sometimes_ping_role'],
            always_role=SETTINGS['always_ping_role'],
            channel_role=SETTINGS['channel_ping_role'],
            pings_channel=SETTINGS['pings_channel'],
        )
        logging.info('Notification handled')
    # Suggestions
    elif message.channel == bot.get_channel(SETTINGS['suggestions_channel']):
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
    with db(SETTINGS['database_path']) as cursor:
        role_is_relevant = cursor.execute('SELECT EXISTS(SELECT id FROM roles WHERE id = ?)', (role.id,)).fetchone()
        if role_is_relevant[0] != 0:
            cursor.execute('DELETE FROM roles WHERE id = ?', (role.id,))
            cursor.execute('UPDATE members SET role = NULL WHERE role = ?', (role.id,))
    logging.info(f'Role {role} deleted')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id != SETTINGS['roles_channel']:
        return
    if SETTINGS['setup_autoroles'] == 1:
        return

    guild = bot.get_guild(SETTINGS['guild'])
    data = extra.get_autorole_data(payload.message_id, AUTOROLES)
    role = extra.get_autorole_role_from_reaction(payload.emoji.name, data, guild)
    await payload.member.add_roles(role)
    logging.info(f'Role {role} added to member {payload.member}')

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id != SETTINGS['roles_channel']:
        return
    if SETTINGS['setup_autoroles'] == 1:
        return

    guild = bot.get_guild(SETTINGS['guild'])
    data = extra.get_autorole_data(payload.message_id, AUTOROLES)
    role = extra.get_autorole_role_from_reaction(payload.emoji.name, data, guild)

    member = guild.get_member(payload.user_id)
    await member.remove_roles(role)
    logging.info(f'Role {role} removed from member {member}')

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *reason):
    reason = ' '.join(reason)
    embed = extra.create_embed({
        'title': 'Ban',
        'description': f'{member.name} has been banned.',
        'Reason': reason,
    })

    await extra.send_dm_embed(embed, member)
    await ctx.send(embed=embed)
    await member.ban(reason=reason)
    logging.info(f'Member {member} banned')

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *reason):
    reason = ' '.join(reason)
    embed = extra.create_embed({
        'title': 'Kick',
        'description': f'{member.name} has been kicked.',
        'Reason': reason,
    })

    await extra.send_dm_embed(embed, member)
    await ctx.send(embed=embed)
    await member.kick(reason=reason)
    logging.info(f'Member {member} kicked')

@bot.command()
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member):
    await ctx.send('Sorry! Muting is not implemented yet')

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *reason):
    reason = ' '.join(reason)
    embed = extra.create_embed({
        'title': 'Warning',
        'description': f'{member.name} has been warned.',
        'Reason': reason,
    })

    await extra.send_dm_embed(embed, member)
    await ctx.send(embed=embed)
    logging.info(f'Member {member} warned')

@bot.command()
@commands.has_permissions(manage_roles=True)
async def approve(ctx, member: discord.Member):
    verified_role = ctx.guild.get_role(SETTINGS['verified_role'])
    notify_role = ctx.guild.get_role(SETTINGS['sometimes_ping_role'])

    if member.bot:
        await member.add_roles(bot_role)
    else:
        await member.add_roles(verified_role, notify_role)

    await ctx.message.add_reaction('👍')
    logging.info(f'Member {member} approved')

@bot.command()
async def role(ctx, color, *name):
    name = ' '.join(name)
    color = extra.hex_to_color(color)

    with db(SETTINGS['database_path']) as cursor:
        role_assigned = cursor.execute('SELECT role FROM members WHERE id = ?', (ctx.author.id,)).fetchone()
        # If no assigned role, create a new one
        if role_assigned[0] == None:
            role = await ctx.guild.create_role(name=name, color=color)
            old_role = None
            new_role = role

            # Set role position above the generic roles
            boundary_role = ctx.guild.get_role(SETTINGS['custom_boundary_role'])
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
    embed = extra.create_embed({
        'title': 'Role update',
        'Name': summary['name'],
        'Color': summary['color'],
    }, inline=False, color=color)
    await ctx.send(embed=embed)

    logging.info(f'Role for member {ctx.author} updated')

bot.run(SETTINGS['token'])

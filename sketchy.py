#!/usr/bin/env python3

import extra
import handlers
import functools
from music import Music
from sqlite_context_manager import db

import json
import logging
import os
from copy import copy
from sys import exit

import sqlite3
import discord
from discord.ext import commands

logging.basicConfig(filename="log.txt", level=logging.INFO)
SETTINGS = extra.import_settings()
extra.setup_db(SETTINGS['database_path'])
AUTOROLES = extra.read_json(SETTINGS['autoroles_path'])

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.presences = True
intents.reactions = True

bot = commands.Bot(command_prefix=SETTINGS['prefix'], intents=intents)
music = Music(SETTINGS['music_path'])

async def run_blocking(blocking_func, *args, **kwargs):
    """Runs a blocking function in a non-blocking way"""
    func = functools.partial(blocking_func, *args, **kwargs)
    return await bot.loop.run_in_executor(None, func)

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

@bot.command(aliases=['connect', 'c'])
async def join(ctx):
    if ctx.message.author.voice:
        channel = ctx.message.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("What do you want me to join?")

@bot.command(aliases=['disconnect', 'dc'])
async def leave(ctx):
    client = ctx.message.guild.voice_client
    if client.is_connected():
        await client.disconnect()
        music.clear()
    else:
        await ctx.send("What do you want me to leave?")

@bot.command(aliases=['p'])
async def play(ctx, *link):
    link = ' '.join(link)
    client = ctx.message.guild.voice_client

    queue = music.get_queue()

    def next(error):
        if music.loop:
            audio = music.play()
            client.play(audio, after=next)
        else:
            if music.skipping:
                music.skipping = False
            else:
                music.dequeue()

            if len(queue) > 0:
                audio = music.play()
                client.play(audio, after=next)

    async with ctx.channel.typing():
        song = await run_blocking(music.enqueue, link)
        embed = extra.create_embed({
            'title': 'Added to queue',
            'Title': f'[{song["title"]}]({song["webpage_url"]})',
        })
        await ctx.send(embed=embed)

    if not client.is_playing():
        audio = music.play()
        client.play(audio, after=next)

@bot.command()
async def pause(ctx):
    client = ctx.message.guild.voice_client
    if client.is_playing():
        client.pause()
        embed = extra.create_embed({
            'title': 'Paused'
        })
        await ctx.send(embed=embed)
    else:
        await ctx.send("There's nothing to pause")

@bot.command(aliases=['unpause'])
async def resume(ctx):
    client = ctx.message.guild.voice_client
    if not client.is_playing():
        client.resume()
        embed = extra.create_embed({
            'title': 'Resumed'
        })
        await ctx.send(embed=embed)
    else:
        await ctx.send("There's nothing to resume")

@bot.command(aliases=['q'])
async def queue(ctx):
    queue = music.get_queue()

    embed = discord.Embed(title='Queue')
    if len(queue) == 0:
        embed.description = 'Empty'
    else:
        names = ["Now playing"] + list(range(1, len(queue)))
        for song, name in zip(queue, names):
            embed.add_field(name=name, value=f'[{song["title"]}]({song["webpage_url"]})', inline=False)

    await ctx.send(embed=embed)

@bot.command(aliases=['l'])
async def loop(ctx):
    async with ctx.channel.typing():
        music.loop = not music.loop

    song = music.get_queue()[0]
    status = 'Looping' if music.loop else 'Stopped looping'
    embed = extra.create_embed({
        'title': 'Queue',
        'description': f'{status} [{song["title"]}]({song["webpage_url"]})'
    })
    await ctx.send(embed=embed)

@bot.command(aliases=['lq'])
async def loop_queue(ctx):
    async with ctx.channel.typing():
        music.loop_queue = not music.loop_queue

    status = 'Looping' if music.loop_queue else 'Stopped looping'
    embed = extra.create_embed({
        'title': 'Queue',
        'description': f'{status} queue'
    })
    await ctx.send(embed=embed)

@bot.command(aliases=['s'])
async def skip(ctx):
    song = music.get_queue()[0]
    music.skipping = True

    async with ctx.channel.typing():
        client = ctx.message.guild.voice_client
        music.dequeue()
        client.stop()

    embed = extra.create_embed({
        'title': 'Queue',
        'description': f'Skipped [{song["title"]}]({song["webpage_url"]})'
    })
    await ctx.send(embed=embed)

@bot.command(aliases=['j'])
async def jump(ctx, number):
    music.skipping = True

    async with ctx.channel.typing():
        client = ctx.message.guild.voice_client
        for skip in range(int(number)):
            music.dequeue()
        client.stop()

    song = music.get_queue()[0]
    embed = extra.create_embed({
        'title': 'Queue',
        'description': f'Skipped to [{song["title"]}]({song["webpage_url"]})'
    })
    await ctx.send(embed=embed)

@bot.command()
async def clear(ctx):
    async with ctx.channel.typing():
        client = ctx.message.guild.voice_client
        client.stop()
        music.clear()

    embed = extra.create_embed({
        'title': 'Queue',
        'description': 'Cleared'
    })
    await ctx.send(embed=embed)

bot.run(SETTINGS['token'])

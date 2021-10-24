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

logging.basicConfig(filename='log.txt', level=logging.INFO)
SETTINGS = extra.read_json('config.json')
extra.setup_db(SETTINGS['paths']['database'])
AUTOROLES = extra.read_json(SETTINGS['paths']['autoroles'])['autoroles']

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.presences = True
intents.reactions = True

bot = commands.Bot(command_prefix=SETTINGS['prefix'], intents=intents)
music = Music(SETTINGS['paths']['music'])

async def run_blocking(blocking_func, *args, **kwargs):
    """Runs a blocking function in a non-blocking way."""
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
    extra.update_members_db(members, SETTINGS['paths']['database'])

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
    await extra.send_dm_embed(embed, member)

    extra.add_member_db(member, SETTINGS['paths']['database'])
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
    data = extra.get_autorole_data(payload.message_id, AUTOROLES)
    role = extra.get_autorole_role_from_reaction(payload.emoji.name, data, guild)
    await payload.member.add_roles(role)
    logging.info(f'Role {role} added to member {payload.member}')

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id != SETTINGS['channels']['roles']:
        return
    if SETTINGS['setup']['autoroles']:
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
    verified_role = ctx.guild.get_role(SETTINGS['roles']['verified'])
    notify_role = ctx.guild.get_role(SETTINGS['roles']['sometimes_ping'])

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

    with db(SETTINGS['paths']['database']) as cursor:
        role_assigned = cursor.execute('SELECT role FROM members WHERE id = ?', (ctx.author.id,)).fetchone()
        # If no assigned role, create a new one
        if role_assigned[0] == None:
            role = await ctx.guild.create_role(name=name, color=color)
            old_role = None
            new_role = role

            # Set role position above the generic roles
            boundary_role = ctx.guild.get_role(SETTINGS['roles']['custom_boundary'])
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

@bot.command()
async def suggest(ctx, *message):
    message = ' '.join(message)
    channel = bot.get_channel(SETTINGS['channels']['suggestions'])

    await channel.send(message)
    await ctx.message.add_reaction('👍')
    logging.info('Suggestion handled')

@bot.command()
async def report(ctx, *message):
    message = ' '.join(message)
    channel = bot.get_channel(SETTINGS['channels']['reports'])
    embed = discord.Embed(title='Report', description=message)

    await channel.send(embed=embed)
    await ctx.message.add_reaction('👍')
    logging.info('Report handled')

@bot.command(aliases=['connect', 'c'])
async def join(ctx):
    if ctx.message.author.voice:
        channel = ctx.message.author.voice.channel
        await channel.connect()
        await ctx.send(embed=extra.create_embed({'title': 'Connected'}))
    else:
        await ctx.send('What do you want me to join?')

@bot.command(aliases=['disconnect', 'dc'])
async def leave(ctx):
    client = ctx.message.guild.voice_client
    if client.is_connected():
        await client.disconnect()
        music = Music(SETTINGS['paths']['music'])
        await ctx.send(embed=extra.create_embed({'title': 'Disconnected'}))
    else:
        await ctx.send('What do you want me to leave?')

@bot.command(aliases=['p'])
async def play(ctx, *link):
    link = ' '.join(link)
    client = ctx.message.guild.voice_client

    queue = music.queue

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
    queue = music.queue

    embed = discord.Embed(title='Queue')
    if music.loop or music.loop_queue or music.shuffle:
        if music.shuffle:
            embed.description = '🔀 Shuffling queue'
        elif music.loop:
            embed.description = '🔂 Looping track'
        elif music.loop_queue:
            embed.description = '🔁 Looping queue'

    names = ['Now playing'] + list(range(1, len(queue)))
    for song, name in zip(queue, names):
        embed.add_field(name=name, value=f'[{song["title"]}]({song["webpage_url"]})', inline=False)

    await ctx.send(embed=embed)

@bot.command(aliases=['nowplaying', 'np'])
async def now_playing(ctx):
    song = music.queue[0]
    embed = extra.create_embed({'title': 'Now playing', 'description': f'[{song["title"]}]({song["webpage_url"]})'})
    await ctx.send(embed=embed)

@bot.command(aliases=['l'])
async def loop(ctx):
    async with ctx.channel.typing():
        music.loop = not music.loop
        music.loop_queue = False
        music.shuffle = False

    song = music.queue[0]
    status = 'Looping' if music.loop else 'Stopped looping'
    embed = extra.create_embed({
        'title': 'Queue',
        'description': f'{status} [{song["title"]}]({song["webpage_url"]})'
    })
    await ctx.send(embed=embed)

@bot.command(aliases=['loopqueue', 'loopq', 'lq'])
async def loop_queue(ctx):
    async with ctx.channel.typing():
        music.loop_queue = not music.loop_queue
        music.loop = False
        music.shuffle = False

    status = 'Looping' if music.loop_queue else 'Stopped looping'
    embed = extra.create_embed({
        'title': 'Queue',
        'description': f'{status} queue'
    })
    await ctx.send(embed=embed)

@bot.command()
async def shuffle(ctx):
    music.shuffle = not music.shuffle
    music.loop = False
    music.loop_queue = False

    status = 'Shuffling' if music.shuffle else 'Stopped shuffling'
    embed = extra.create_embed({
        'title': 'Queue',
        'description': f'{status} queue',
    })
    await ctx.send(embed=embed)

@bot.command(aliases=['s'])
async def skip(ctx):
    song = music.queue[0]
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

    song = music.queue[0]
    embed = extra.create_embed({
        'title': 'Queue',
        'description': f'Skipped to [{song["title"]}]({song["webpage_url"]})'
    })
    await ctx.send(embed=embed)

@bot.command(aliases=['rm', 'x'])
async def remove(ctx, number):
    song = music.queue.pop(int(number))
    embed = extra.create_embed({
        'title': 'Queue',
        'description': f'Removed [{song["title"]}]({song["webpage_url"]})'
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

from database import db

import functools
import json
import logging
import os
import re
from datetime import timedelta

import discord
import sqlite3

def read_json(path):
    """Read JSON from a file into a Python object."""
    with open(path, 'r') as data_file:
        json_data = data_file.read()
        return json.loads(json_data)

async def run_blocking(blocking_func, bot, *args, **kwargs):
    """Runs a blocking function in a non-blocking way."""
    func = functools.partial(blocking_func, *args, **kwargs)
    return await bot.loop.run_in_executor(None, func)

def read_file(path):
    with open(path, 'r') as file:
        return file.read()

def has_url(text):
    """Checks whether a piece of text contains a URL."""
    link_expression = re.compile(r'https?://[a-z0-9\.]+\.[a-z0-9]')
    contains_link = link_expression.search(text.lower()) != None
    return contains_link

def extract_time(current_time, text):
    """Attempt to extract a relative point in time from a string."""
    matches = re.match(r'^(\d+)([mhdwy])$', text)
    duration = int(matches.group(1))
    unit = matches.group(2)

    new_time = current_time
    if unit == 'm':
        new_time += timedelta(minutes=duration)
    elif unit == 'd':
        new_time += timedelta(days=duration)
    elif unit == 'w':
        new_time += timedelta(weeks=duration)
    elif unit == 'y':
        new_time += timedelta(days=duration*365)

    return new_time

def compare_roles(old_role, new_role):
    """Compare name and color of two roles and return a dictionary of strings showing the changes."""
    if old_role:
        if old_role.name == new_role.name:
            name_message = new_role.name
        else:
            name_message = f'{old_role.name} → {new_role.name}'

        if old_role.color == new_role.color:
            color_message = new_role.color
        else:
            color_message = f'{str(old_role.color)} → {str(new_role.color)}'
    else:
        name_message = new_role.name
        color_message = new_role.color

    return {"name": name_message, "color": color_message}

def create_embed(options, inline=True, color=None):
    """Create an embed from a dictionary of options."""
    if color == None:
        embed = discord.Embed()
    else:
        embed = discord.Embed(color=color)

    if 'title' in options:
        embed.title = options.pop('title')
    if 'description' in options:
        embed.description = options.pop('description')

    for name, value in options.items():
        embed.add_field(name=name, value=value, inline=inline)

    return embed

async def send_dm_embed(embed, recipient):
    """Send an embed to a member."""
    dm = await recipient.create_dm()
    await dm.send(embed=embed)

def hex_to_color(hex):
    """Generate a Discord color object from a hex triplet string."""
    red, green, blue = bytes.fromhex(hex.lstrip('#'))
    return discord.Color.from_rgb(red, green, blue)

def get_autorole_data(message_id, autoroles):
    """Get data about an auto-role from its message ID."""
    for autorole in autoroles:
        if message_id == autorole['message']:
            return autorole

def get_autorole_role_from_reaction(emoji, autorole_data, guild):
    """Get the role represented by an auto-role reaction."""
    for reaction, role in zip(autorole_data['reactions'], autorole_data['roles']):
        if emoji == reaction:
            return guild.get_role(role)

import os
import re
import json
import sqlite3
from typing import Dict, Tuple

import discord

def setup_db(path):
    """Sets up a database if it doesn't already exist."""
    if not os.path.exists(path):
        connection = sqlite3.connect(path)
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

def read_json(path):
    """Read JSON from a file into a Python object."""
    with open(path, 'r') as autoroles_file:
        autoroles_json = autoroles_file.read()
        return json.loads(autoroles_json)['autoroles']

def update_members_db(members, db_path):
    """Update 'members' database table from a list of members."""
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    for member in members:
        member_exists = cursor.execute('SELECT EXISTS(SELECT id FROM members WHERE id = ?)', (member.id,)).fetchone()
        if member_exists[0] == 0:
            cursor.execute('INSERT INTO members(id) VALUES(?)', (member.id,))

    connection.commit()
    connection.close()
    print('Database updated!')

def add_member_db(member, db_path):
    """Add a new member to the database."""
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute('INSERT INTO members(id) VALUES(?)', (member.id,))

    connection.commit()
    connection.close()

def has_url(text):
    """Checks whether a piece of text contains a URL."""
    link_expression = re.compile(r'https?://[a-z0-9\.]+\.[a-z0-9]')
    contains_link = link_expression.match(text.lower()) != None
    return contains_link

def compare_roles(old_role, new_role):
    """Compare name and color of two roles and return a dictionary of strings showing the changes."""
    if old_role.name == new_role.name:
        name_message = new_role.name
    else:
        name_message = f'{old_role.name} → {new_role.name}'

    if old_role.color == new_role.color:
        color_message = new_role.color
    else:
        color_message = f'{str(old_role.color)} → {str(new_role.color)}'

    return {"name": name_message, "color": color_message}

async def send_dm_embed(embed, recipient):
    """Send an embed to a member."""
    dm = await recipient.create_dm()
    await dm.send(embed=embed)

async def handle_dm(bot, message, reports_channel_id):
    """Handler for direct messages received by the bot."""
    if message.author != bot.user:
        channel = bot.get_channel(reports_channel_id)
        embed = discord.Embed(title='Report', description=message.content)
        await channel.send(embed=embed)
        await message.add_reaction('👍')

async def handle_notifications(message, *, sometimes_role, always_role):
    """Handler for notifications that the bot must deliver."""
    if has_url(message.content):
        return

    for member in message.guild.members:
        try:
            roles = member.roles
            # Don't notify offline users
            if message.guild.get_role(sometimes_role) in roles:
                if member.status == discord.Status.offline:
                    continue
            elif message.guild.get_role(always_role) in roles:
                pass

            # Format message
            embed = discord.Embed(title='A game is being hosted!', description=message.content)
            embed.add_field(name="Host", value=message.author.name)

            await send_dm_embed(embed, member)
        except:
            pass

async def handle_suggestions(message):
    """Handler for messages sent in the suggestions channel."""
    await message.add_reaction('👍')
    await message.add_reaction('👎')

async def handle_mentions(message):
    """Handler for messages sent in the suggestions channel."""
    await message.add_reaction('🤍')
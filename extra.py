from sqlite_context_manager import db

import os
import logging
import re
import json
import sqlite3
from dotenv import load_dotenv

import discord

def setup_db(path):
    """Sets up a database if it doesn't already exist."""
    if not os.path.exists(path):
        with db(path) as cursor:
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.execute('''CREATE TABLE roles
                            (id INTEGER PRIMARY KEY)''')
            cursor.execute('''CREATE TABLE members
                            (id INTEGER PRIMARY KEY,
                            role INTEGER,
                            FOREIGN KEY(role) REFERENCES roles(id) ON DELETE SET NULL)''')
            logging.info('Set up database!')

def read_json(path):
    """Read JSON from a file into a Python object."""
    with open(path, 'r') as autoroles_file:
        autoroles_json = autoroles_file.read()
        return json.loads(autoroles_json)['autoroles']

def update_members_db(members, db_path):
    """Update 'members' database table from a list of members."""
    with db(db_path) as cursor:
        for member in members:
            member_exists = cursor.execute('SELECT EXISTS(SELECT id FROM members WHERE id = ?)', (member.id,)).fetchone()
            if member_exists[0] == 0:
                cursor.execute('INSERT INTO members(id) VALUES(?)', (member.id,))
        logging.info('Database updated!')

def add_member_db(member, db_path):
    """Add a new member to the database."""
    with db(db_path) as cursor:
        cursor.execute('INSERT INTO members(id) VALUES(?)', (member.id,))

def has_url(text):
    """Checks whether a piece of text contains a URL."""
    link_expression = re.compile(r'https?://[a-z0-9\.]+\.[a-z0-9]')
    contains_link = link_expression.search(text.lower()) != None
    return contains_link

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

def import_settings():
    load_dotenv()
    return {
        "token": os.getenv('SKETCHY_TOKEN'),
        "guild": int(os.getenv('SKETCHY_GUILD')),
        "database_path": os.getenv('SKETCHY_DATABASE_PATH'),
        "autoroles_path": os.getenv('SKETCHY_AUTOROLES_PATH'),
        "prefix": os.getenv('SKETCHY_PREFIX'),
        "setup_autoroles": int(os.getenv('SKETCHY_SETUP_AUTOROLES')),
        "games_channel": int(os.getenv('SKETCHY_GAMES_CHANNEL')),
        "pings_channel": int(os.getenv('SKETCHY_PINGS_CHANNEL')),
        "reports_channel": int(os.getenv('SKETCHY_REPORTS_CHANNEL')),
        "roles_channel": int(os.getenv('SKETCHY_ROLES_CHANNEL')),
        "suggestions_channel": int(os.getenv('SKETCHY_SUGGESTIONS_CHANNEL')),
        "verified_role": int(os.getenv('SKETCHY_VERIFIED_ROLE')),
        "bot_role": int(os.getenv('SKETCHY_BOT_ROLE')),
        "always_ping_role": int(os.getenv('SKETCHY_ALWAYS_PING_ROLE')),
        "sometimes_ping_role": int(os.getenv('SKETCHY_SOMETIMES_PING_ROLE')),
        "channel_ping_role": int(os.getenv('SKETCHY_CHANNEL_PING_ROLE')),
        "custom_boundary_role": int(os.getenv('SKETCHY_CUSTOM_BOUNDARY_ROLE')),
    }

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

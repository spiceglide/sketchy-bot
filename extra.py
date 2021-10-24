import os
import re
import json
import sqlite3

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
    if old_role.name == new_role.name:
        name_message = new_role.name
    else:
        name_message = f'{old_role.name} -> {new_role.name}'

    if old_role.color == new_role.color:
        color_message = new_role.color
    else:
        color_message = f'{str(old_role.color)} -> {str(new_role.color)}'

    return {"name": name_message, "color": color_message}
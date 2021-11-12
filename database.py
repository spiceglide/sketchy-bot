import logging
import os

import sqlite3

class db():
    """A SQLite context manager."""
    def __init__(self, file='data.db'):
        self.file = file
    def __enter__(self):
        self.connection = sqlite3.connect(self.file)
        return self.connection.cursor()
    def __exit__(self, type, value, traceback):
        self.connection.commit()
        self.connection.close()

def setup(path):
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

def update_members(members, db_path):
    """Update 'members' database table from a list of members."""
    with db(db_path) as cursor:
        for member in members:
            member_exists = cursor.execute('SELECT EXISTS(SELECT id FROM members WHERE id = ?)', (member.id,)).fetchone()
            if member_exists[0] == 0:
                cursor.execute('INSERT INTO members(id) VALUES(?)', (member.id,))
        logging.info('Database updated!')

def add_member(member, db_path):
    """Add a new member to the database."""
    with db(db_path) as cursor:
        cursor.execute('INSERT INTO members(id) VALUES(?)', (member.id,))
import common

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
            query_list = [
                'queries/init.sql',
                'queries/create-table-roles.sql',
                'queries/create-table-members.sql',
                'queries/create-table-reminders.sql',
            ]

            for query_path in query_list:
                query = common.read_file(query_path)
                cursor.execute(query)

            logging.info('Set up database!')

def update_members(members, db_path):
    """Update 'members' database table from a list of members."""
    with db(db_path) as cursor:
        for member in members:
            query = common.read_file('queries/exists-member.sql')
            member_exists = cursor.execute(query, (member.id,)).fetchone()
            if member_exists[0] == 0:
                query = common.read_file('queries/add-member.sql')
                cursor.execute(query, (member.id,))
        logging.info('Database updated!')

def add_member(member, db_path):
    """Add a new member to the database."""
    with db(db_path) as cursor:
        query = common.read_file('queries/add-member.sql')
        cursor.execute(query, (member.id,))

def add_reminder(title, member, time, db_path):
    """Add a new reminder to the database."""
    member = member.id
    time = int(time.timestamp())

    with db(db_path) as cursor:
        query = common.read_file('queries/add-reminder.sql')
        cursor.execute(query, (title, member, time))

def get_reminders(limit_time, db_path):
    """Get all the reminders before a specified time."""
    limit_time = int(limit_time.timestamp())

    with db(db_path) as cursor:
        query = common.read_file('queries/select-reminders.sql')
        cursor.execute(query, (limit_time,))
        return cursor.fetchall()

def delete_reminders(limit_time, db_path):
    """Delete reminders before a specified time."""
    with db(db_path) as cursor:
        query = common.read_file('queries/delete-reminders.sql')
        cursor.execute(query, (limit_time,))
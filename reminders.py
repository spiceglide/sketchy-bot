import common
import handlers
import database

import asyncio
import logging
from copy import copy
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

logging.basicConfig(filename='log.txt', level=logging.INFO)

class Reminders(commands.Cog):
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
    
    async def poll(bot, settings):
        INTERVAL = 60
        db_path = settings['paths']['database']
        channel = bot.get_channel(settings['channels']['reminders'])

        while True:
            now = datetime.now(timezone.utc)
            soon = now + timedelta(seconds=INTERVAL)

            # Check for reminders
            try:
                reminders = database.get_reminders(soon, db_path)
                if reminders:
                    for reminder in reminders:
                        title = reminder[0]
                        member = bot.get_user(reminder[1])

                        await channel.send(embed=common.create_embed({
                            'title': 'Reminder',
                            'description': title,
                        }))

                        logging.info("Sent reminder!")
                    
                    database.delete_reminders(soon, db_path)
            except:
                logging.error("Failed to send reminder")

            # Check for birthdays
            try:
                if now.day != soon.day:
                    birthdays = database.get_birthdays(soon, db_path)
                    if birthdays:

                        for birthday in birthdays:
                            member = bot.get_user(birthday[0])

                            await channel.send(embed=common.create_embed({
                                'title': 'Birthday',
                                'description': f'Happy birthday, {member.mention}!',
                            }))
                    
                            logging.info("Sent birthday wishes!")
            except:
                logging.error("Failed to send birthday wishes")

            await asyncio.sleep(INTERVAL)

    @commands.command(aliases=['reminder', 'remindme'])
    async def remind(self, ctx, time, *title):
        """Set a reminder."""
        title = ' '.join(title)
        member = ctx.author

        time = common.extract_time(datetime.now(timezone.utc), time)
        db_path = self.settings['paths']['database']
        database.add_reminder(title, member, time, db_path)

        await ctx.message.add_reaction('👍')
        logging.info('Set reminder!')

    @commands.command(aliases=['bday', 'bd'])
    async def birthday(self, ctx, date):
        """Set your birthday to get automatic wishes."""
        member = ctx.author
        
        # YYYY-MM-DD
        try:
            date = datetime.strptime(date, '%Y-%m-%d')
        # MM-DD
        except:
            date = f'0000-{date}'
            date = datetime.strptime(date, f'%m-%d')

        db_path = self.settings['paths']['database']
        database.add_birthday(member, date, db_path)

        await ctx.message.add_reaction('👍')
        logging.info('Set birthday!')

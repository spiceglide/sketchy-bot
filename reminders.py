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

                        embed = common.create_embed({
                            'title': 'Reminder',
                            'description': title,
                        })
                        await common.send_dm_embed(embed, member)
                    
                    database.delete_reminders(soon, db_path)
            except:
                pass

            # Check for birthdays
            try:
                if now.minute != soon.minute:
                    birthdays = database.get_birthdays(soon, db_path)

                    # Every day is Sammy day
                    sammy = bot.get_user(439512171836211230)  # temp
                    #sammy = bot.get_user(331886521647104002)
                    await channel.send(embed=common.create_embed({
                        'title': 'Birthday',
                        'description': f'Happy birthday, {sammy.mention}!',
                    }))

                    if birthdays:
                        for birthday in birthdays:
                            member = bot.get_user(birthday[0])

                        await channel.send(embed=common.create_embed({
                            'title': 'Birthday',
                            'description': f'Happy birthday, {member.mention}!',
                        }))
            except:
                pass

            await asyncio.sleep(INTERVAL)

    @commands.command()
    async def remind(self, ctx, time, *title):
        """Set a reminder."""
        title = ' '.join(title)
        member = ctx.author

        time = common.extract_time(datetime.now(timezone.utc), time)
        db_path = self.settings['paths']['database']
        database.add_reminder(title, member, time, db_path)

    @commands.command()
    async def birthday(self, ctx, date):
        """Set your birthday to get automatic wishes."""
        date = datetime.strptime(date, '%Y-%m-%d')
        member = ctx.author
        
        db_path = self.settings['paths']['database']
        database.add_birthday(member, date, db_path)
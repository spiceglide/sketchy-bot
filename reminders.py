import common
import handlers
from database import db

import asyncio
import logging
from copy import copy
from datetime import datetime

import discord
from discord.ext import commands

logging.basicConfig(filename='log.txt', level=logging.INFO)

class Reminders(commands.Cog):
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
    
    async def poll(settings):
        while True:
            now = datetime.now().strftime('%H:%M:%S')
            print(f'Polled at {now}')
            await asyncio.sleep(60)

    @commands.command()
    async def remind(self, ctx, time, *title):
        """Set a reminder."""
        title = ' '.join(title)
        member = ctx.author

        time = common.extract_time(datetime.now(), time)

    @commands.command()
    async def birthday(self, ctx):
        """Set your birthday to get automatic wishes."""
        # TODO
        pass
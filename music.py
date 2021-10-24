import common

import os
import random
import logging

import discord
from discord.ext import commands
from yt_dlp import YoutubeDL

logging.basicConfig(filename='log.txt', level=logging.INFO)

class Music(commands.Cog):
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.path = settings['paths']['music']

        self.refresh()

        self.ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
        self.youtube_dl_options = {'format': 'bestaudio', 'outtmpl': f'{self.path}/%(id)s', 'quiet': True}

    def refresh(self):
        self.queue = []
        self.loop = False
        self.loop_queue = False
        self.shuffle = False
        self.skipping = False
        self.nightcore = False
        self.bass_boosted = False

    @commands.command(aliases=['connect', 'c'])
    async def join(self, ctx):
        if ctx.message.author.voice:
            channel = ctx.message.author.voice.channel
            await channel.connect()
            await ctx.send(embed=common.create_embed({'title': 'Connected'}))
        else:
            await ctx.send('What do you want me to join?')

    @commands.command(aliases=['disconnect', 'dc'])
    async def leave(self, ctx):
        client = ctx.message.guild.voice_client
        if client.is_connected():
            await client.disconnect()
            self.refresh()
            await ctx.send(embed=common.create_embed({'title': 'Disconnected'}))
        else:
            await ctx.send('What do you want me to leave?')

    @commands.command(aliases=['p'])
    async def play(self, ctx, *link):
        link = ' '.join(link)
        client = ctx.message.guild.voice_client

        queue = self.queue

        def next(error):
            if self.loop:
                audio = self.old_play()
                client.play(audio, after=next)
            else:
                if self.skipping:
                    self.skipping = False
                else:
                    self.old_dequeue()

                if len(queue) > 0:
                    audio = self.old_play()
                    client.play(audio, after=next)

        async with ctx.channel.typing():
            song = await common.run_blocking(self.old_enqueue, self.bot, link)

        embed = common.create_embed({
            'title': 'Added to queue',
            'Title': f'[{song["title"]}]({song["webpage_url"]})',
        })
        await ctx.send(embed=embed)

        if not client.is_playing():
            audio = self.old_play()
            client.play(audio, after=next)

    @commands.command()
    async def pause(self, ctx):
        client = ctx.message.guild.voice_client
        if client.is_playing():
            client.pause()
            embed = common.create_embed({
                'title': 'Paused'
            })
            await ctx.send(embed=embed)
        else:
            await ctx.send("There's nothing to pause")

    @commands.command(aliases=['unpause'])
    async def resume(self, ctx):
        client = ctx.message.guild.voice_client
        if not client.is_playing():
            client.resume()
            embed = common.create_embed({
                'title': 'Resumed'
            })
            await ctx.send(embed=embed)
        else:
            await ctx.send("There's nothing to resume")

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        queue = self.queue
        embed = discord.Embed(title='Queue', description='')

        if self.nightcore or self.bass_boosted:
            if self.nightcore:
                embed.description += '\n📻 Nightcore'
            elif self.bass_boosted:
                embed.description += '\n📻 Bass boosted'

        if self.loop or self.loop_queue or self.shuffle:
            if self.shuffle:
                embed.description += '\n🔀 Shuffling queue'
            elif self.loop:
                embed.description += '\n🔂 Looping track'
            elif self.loop_queue:
                embed.description += '\n🔁 Looping queue'

        names = ['Now playing'] + list(range(1, len(queue)))
        for song, name in zip(queue, names):
            embed.add_field(name=name, value=f'[{song["title"]}]({song["webpage_url"]})', inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=['nowplaying', 'np'])
    async def now_playing(self, ctx):
        song = self.queue[0]
        embed = common.create_embed({'title': 'Now playing', 'description': f'[{song["title"]}]({song["webpage_url"]})'})
        await ctx.send(embed=embed)

    @commands.command(aliases=['l'])
    async def loop(self, ctx):
        async with ctx.channel.typing():
            self.loop = not self.loop
            self.loop_queue = False
            self.shuffle = False

        song = self.queue[0]
        status = 'Looping' if self.loop else 'Stopped looping'
        embed = common.create_embed({
            'title': 'Queue',
            'description': f'{status} [{song["title"]}]({song["webpage_url"]})'
        })
        await ctx.send(embed=embed)

    @commands.command(aliases=['loopqueue', 'loopq', 'lq'])
    async def loop_queue(self, ctx):
        async with ctx.channel.typing():
            self.loop_queue = not self.loop_queue
            self.loop = False
            self.shuffle = False

        status = 'Looping' if self.loop_queue else 'Stopped looping'
        embed = common.create_embed({
            'title': 'Queue',
            'description': f'{status} queue'
        })
        await ctx.send(embed=embed)

    @commands.command()
    async def shuffle(self, ctx):
        self.shuffle = not self.shuffle
        self.loop = False
        self.loop_queue = False

        status = 'Shuffling' if self.shuffle else 'Stopped shuffling'
        embed = common.create_embed({
            'title': 'Queue',
            'description': f'{status} queue',
        })
        await ctx.send(embed=embed)

    @commands.command(aliases=['nc', 'weeb'])
    async def nightcore(self, ctx):
        self.nightcore = not self.nightcore
        self.bass_boosted = False

        status = 'ON' if self.nightcore else 'OFF'
        embed = common.create_embed({
            'title': 'Queue',
            'description': f'Nightcore {status}',
        })
        await ctx.send(embed=embed)

    @commands.command(aliases=['bassboost', 'bass_boosted', 'bassboosted', 'bass'])
    async def bass_boost(self, ctx):
        self.bass_boosted = not self.bass_boosted
        self.nightcore = False

        status = 'ON' if self.bass_boosted else 'OFF'
        embed = common.create_embed({
            'title': 'Queue',
            'description': f'Bass boost {status}',
        })
        await ctx.send(embed=embed)

    @commands.command(aliases=['s'])
    async def skip(self, ctx):
        song = self.queue[0]
        self.skipping = True

        async with ctx.channel.typing():
            client = ctx.message.guild.voice_client
            self.old_dequeue()
            client.stop()

        embed = common.create_embed({
            'title': 'Queue',
            'description': f'Skipped [{song["title"]}]({song["webpage_url"]})'
        })
        await ctx.send(embed=embed)

    @commands.command(aliases=['j'])
    async def jump(self, ctx, number):
        self.skipping = True

        async with ctx.channel.typing():
            client = ctx.message.guild.voice_client
            for skip in range(int(number)):
                self.old_dequeue()
            client.stop()

        song = self.queue[0]
        embed = common.create_embed({
            'title': 'Queue',
            'description': f'Skipped to [{song["title"]}]({song["webpage_url"]})'
        })
        await ctx.send(embed=embed)

    @commands.command(aliases=['rm', 'x'])
    async def remove(self, ctx, number):
        song = self.queue.pop(int(number))
        embed = common.create_embed({
            'title': 'Queue',
            'description': f'Removed [{song["title"]}]({song["webpage_url"]})'
        })
        await ctx.send(embed=embed)

    @commands.command()
    async def clear(self, ctx):
        async with ctx.channel.typing():
            client = ctx.message.guild.voice_client
            client.stop()
            self.old_clear()

        embed = common.create_embed({
            'title': 'Queue',
            'description': 'Cleared'
        })
        await ctx.send(embed=embed)

    def old_enqueue(self, link):
        with YoutubeDL(self.youtube_dl_options) as ydl:
            if common.has_url(link):
                info = ydl.extract_info(link)

                if 'entries' in info:
                    for track in info['entries']:
                        self.queue.append(track)
                else:
                    self.queue.append(info)
            else:
                info = ydl.extract_info(f'ytsearch1:{link}')['entries'][0]
                self.queue.append(info)

        return info
        
    def old_dequeue(self):
        if self.loop:
            pass
        elif self.loop_queue:
            song = self.queue.pop(0)
            self.queue.append(song)
        elif self.shuffle:
            index = random.randrange(len(self.queue) - 1)
            song = self.queue.pop(index)
            self.queue.insert(0, song)
        else:
            song = self.queue.pop(0)
    
    def old_play(self):
        current_song = self.queue[0]
        song_path = f'{self.path}/{current_song["id"]}'

        if self.nightcore:
            if not os.path.exists(f'{song_path}-nightcore'):
                filter = 'aformat=channel_layouts=stereo,asetrate=44100*4/3'
                os.system(f'ffmpeg -i {song_path} -af "{filter}" -f webm -nostats -loglevel 0 {song_path}-nightcore')
            song_path += '-nightcore'
        elif self.bass_boosted:
            if not os.path.exists(f'{song_path}-bass'):
                filter = 'bass=g=12'
                os.system(f'ffmpeg -i {song_path} -af "{filter}" -f webm -nostats -loglevel 0 {song_path}-bass')
            song_path += '-bass'

        return discord.FFmpegPCMAudio(song_path, options=self.ffmpeg_options)

    def old_clear(self):
        self.queue = []
        for file in os.listdir(self.path):
            os.remove(f'{self.path}/{file}')
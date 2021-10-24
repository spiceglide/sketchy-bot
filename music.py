import os
import functools
import asyncio
from extra import has_url

from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL

def to_thread(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

class Music:
    def __init__(self, path):
        self.path = path
        self.queue = []
        self.loop = False

        self.ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
        self.youtube_dl_options = {'format': 'bestaudio', 'outtmpl': f'{path}/%(id)s', 'quiet': True}

    @to_thread
    def enqueue(self, link):
        with YoutubeDL(self.youtube_dl_options) as ydl:
            if has_url(link):
                info = ydl.extract_info(link)
            else:
                info = ydl.extract_info(f'ytsearch1:{link}')['entries'][0]

            self.queue.append(info)
            ydl.download([info['webpage_url']])
            return info
        
    def dequeue(self):
        self.queue.pop(0)
    
    def play(self):
        current_song = self.queue[0]
        return FFmpegPCMAudio(f'{self.path}/{current_song["id"]}', options=self.ffmpeg_options)

    def skip(self):
        self.dequeue()
        self.play()
    
    def clear(self):
        self.queue = []
        for file in os.listdir(self.path):
            os.remove(f'{self.path}/{file}')

    def toggle_loop(self):
        self.loop = not self.loop

    def is_looping(self):
        return self.loop
    
    def get_queue(self):
        return self.queue

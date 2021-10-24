from extra import has_url

import os

from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL

class Music:
    def __init__(self, path):
        self.path = path
        self.queue = []
        self.loop = False
        self.loop_queue = False
        self.shuffle = False
        self.skipping = False

        self.ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
        self.youtube_dl_options = {'format': 'bestaudio', 'outtmpl': f'{path}/%(id)s', 'quiet': True}

    def enqueue(self, link):
        with YoutubeDL(self.youtube_dl_options) as ydl:
            if has_url(link):
                info = ydl.extract_info(link)
            else:
                info = ydl.extract_info(f'ytsearch1:{link}')['entries'][0]
            self.queue.append(info)

        return info
        
    def dequeue(self):
        if self.shuffle:
            self.queue = random.shuffle(self.queue)
        else:
            song = self.queue.pop(0)
            
            if self.loop_queue:
                self.queue.append(song)
    
    def play(self):
        current_song = self.queue[0]
        song_path = f'{self.path}/{current_song["id"]}'
        return FFmpegPCMAudio(song_path, options=self.ffmpeg_options)

    def clear(self):
        self.queue = []
        for file in os.listdir(self.path):
            os.remove(f'{self.path}/{file}')
    
    def get_queue(self):
        return self.queue

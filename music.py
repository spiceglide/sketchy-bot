import os
from threading import Thread
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from youtube_dl import YoutubeDL

class Music:
    def __init__(self, path):
        self.path = path
        self.queue = []

        self.ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
        self.youtube_dl_options = {'format': 'bestaudio', 'outtmpl': f'{path}/%(id)s'}

    def enqueue(self, link):
        with YoutubeDL(self.youtube_dl_options) as ydl:
            info = ydl.extract_info(link)
            self.queue.append(info)

            ydl.download([link])
        
    def dequeue(self):
        self.queue.pop(0)
    
    def play(self):
        current_song = self.queue[0]
        return FFmpegPCMAudio(f'{self.path}/{current_song["id"]}')
    
    def get_queue(self):
        return self.queue
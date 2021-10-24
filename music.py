from common import has_url

import os
import random

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
        self.nightcore = False
        self.bass_boosted = False

        self.ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
        self.youtube_dl_options = {'format': 'bestaudio', 'outtmpl': f'{path}/%(id)s', 'quiet': True}

    def enqueue(self, link):
        with YoutubeDL(self.youtube_dl_options) as ydl:
            if has_url(link):
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
        
    def dequeue(self):
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
    
    def play(self):
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

        return FFmpegPCMAudio(song_path, options=self.ffmpeg_options)

    def clear(self):
        self.queue = []
        for file in os.listdir(self.path):
            os.remove(f'{self.path}/{file}')
import os
from youtube_dl import YoutubeDL
from discord import FFmpegPCMAudio, PCMVolumeTransformer

class Music:
    def __init__(self, path):
        self.path = path
        self.ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
        #self.youtube_dl_options = {'format': 'bestaudio', 'outtmpl': f'{path}/%(id)s'}
        self.youtube_dl_options = {'format': 'worstaudio', 'outtmpl': f'{path}/song'}
    def get_music(self, link):
        try:
            os.remove(f'{self.path}/song')
        except:
            pass

        with YoutubeDL(self.youtube_dl_options) as ydl:
            ydl.download([link])
        return FFmpegPCMAudio(f'{self.path}/song')
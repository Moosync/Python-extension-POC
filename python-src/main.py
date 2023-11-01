#!/usr/bin/env python3

import asyncio
from moosyncLib.lib import start, event_handler
from moosyncLib.data import Song
from moosyncLib.api import api
from moosyncLib.data import ContextMenuItem

from urllib.parse import urlparse, parse_qs
from yt_dlp import YoutubeDL
import os

def video_id(value):
    query = urlparse(value)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            p = parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    return None

async def on_started():
    await api.set_context_menu_item([ContextMenuItem(type="SONGS", label="Try download", handler=context_menu_handler)])
    await api.set_context_menu_item([ContextMenuItem(type="PLAYLIST_CONTENT", label="Try download", handler=context_menu_handler)])
    
async def context_menu_handler(songs: list[dict]):
    urls = []
    s = []
    if len(songs) > 0:
        for song in songs:
            if song["type"] == "YOUTUBE" and song["playbackUrl"] is not None:
                if song["playbackUrl"].startswith("https://"):
                    urls.append(song["playbackUrl"])
                else:
                    urls.append(f"https://www.youtube.com/watch?v={song['playbackUrl']}")
                    
                s.append(song)

    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
        "paths": { 
            "home": "/home/ovenoboyo/ytdl"
        },
        "outtmpl": {
            "default": "%(id)s"
        }
    }
    with YoutubeDL(ydl_opts) as ydl:
        await api.show_toast("Downloading songs", 3000, "info")
        i = 0
        for url in urls:
            error = ydl.download(url)
            if error == 0:
                print(video_id(url), f"/home/ovenoboyo/ytdl/{video_id(url)}", flush=True)
                s[i]["path"] = f"/home/ovenoboyo/ytdl/{video_id(url)}.m4a"
                s[i]["type"] = "LOCAL"
                await api.update_song(s[i])
            print( "error code: ", error, flush=True)
            i += 1

async def main():
    await event_handler.add_listener("onStarted", on_started, [])
    await start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

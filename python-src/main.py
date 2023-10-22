#!/usr/bin/env python3

import asyncio
import uuid
from moosyncLib.lib import start, event_handler, api

async def on_started():
    currentSong = await api.getCurrentSong()
    print("current song", currentSong, flush=True)

def on_volume_changed(new_volume):
    print('Volume changed to', new_volume, flush=True)
    
def on_song_changed(song):
    print('Song changed to', song, flush=True)
    
def requested_playlists(invalidateCache):
    return {
        "playlists": [{
            "playlist_id": str(uuid.uuid4()),
            "playlist_name": "Playlist from python",
        }]
    }


async def main():
    await event_handler.add_listener("volumeChanged", on_volume_changed)
    await event_handler.add_listener("songChanged", on_song_changed)
    await event_handler.add_listener("requestedPlaylists", requested_playlists)
    await event_handler.add_listener("onStarted", on_started)
    
    await start()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

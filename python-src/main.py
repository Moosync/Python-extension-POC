#!/usr/bin/env python3

from moosyncLib.lib import start, event_handler

def on_volume_changed(new_volume):
    print('Volume changed to', new_volume, flush=True)
    
def on_song_changed(song):
    print('Song changed to', song, flush=True)


if __name__ == '__main__':
    event_handler.add_listener("volumeChanged", on_volume_changed)
    event_handler.add_listener("songChanged", on_song_changed)
    
    start()

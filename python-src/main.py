#!/usr/bin/env python3

import asyncio
import sys
from moosyncLib.lib import connect_client, start, event_handler
from moosyncLib.api import api
from moosyncLib.data import ContextMenuItem, ExtensionPreferenceGroup

import typing
from urllib.parse import urlparse, parse_qs
from yt_dlp import YoutubeDL
import os

__dirname = sys.argv[1]
default_store_path = os.path.join(__dirname, "downloads")


def video_id(value):
    query = urlparse(value)
    if query.hostname == "youtu.be":
        return query.path[1:]
    if query.hostname in ("www.youtube.com", "youtube.com"):
        if query.path == "/watch":
            p = parse_qs(query.query)
            return p["v"][0]
        if query.path[:7] == "/embed/":
            return query.path.split("/")[2]
        if query.path[:3] == "/v/":
            return query.path.split("/")[2]
    return None


async def on_started():
    print("Started ytdlp")
    await api.set_context_menu_item(
        [
            ContextMenuItem(
                type="SONGS", label="Try download", handler=context_menu_handler
            )
        ]
    )
    await api.set_context_menu_item(
        [
            ContextMenuItem(
                type="PLAYLIST_CONTENT",
                label="Try download",
                handler=context_menu_handler,
            )
        ]
    )

    await api.add_user_preferences(
        ExtensionPreferenceGroup(
            key="path",
            title="Download path",
            default=default_store_path,
            type="FilePicker",
        )
    )


async def context_menu_handler(songs: typing.Optional[list[dict]]):
    if songs is not None and len(songs) > 0:
        urls = []
        s = []
        store_path = await api.get_preferences("path")
        if store_path is None:
            store_path = default_store_path
        for song in songs:
            if song["type"] == "YOUTUBE" and song["playbackUrl"] is not None:
                if song["playbackUrl"].startswith("https://"):
                    urls.append(
                        f"https://www.youtube.com/watch?v={video_id(song['playbackUrl'])}"
                    )
                else:
                    urls.append(
                        f"https://www.youtube.com/watch?v={song['playbackUrl']}"
                    )

                s.append(song)

        ydl_opts = {
            "format": "m4a/bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                }
            ],
            "paths": {"home": store_path},
            "outtmpl": {"default": "%(id)s"},
        }

        with YoutubeDL(ydl_opts) as ydl:
            await api.show_toast("Downloading songs", 3000, "info")
            i = 0
            for url in urls:
                error = ydl.download(url)
                if error == 0:
                    s[i]["path"] = os.path.join(store_path, f"{video_id(url)}.m4a")
                    await api.update_song(s[i])
                    await api.show_toast(f"Downloaded {s[i]['title']}", 1000, "info")
                i += 1


async def main():
    connect_client()
    print("Starting extension")
    await event_handler.add_listener("onStarted", on_started, [])
    await start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

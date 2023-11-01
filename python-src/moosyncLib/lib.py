import json
import asyncio
from typing import Callable, Literal
import inspect

from moosyncLib.utils import EnhancedJSONEncoder, generate_event_request, client
from moosyncLib.api import api
from moosyncLib.data import (
    Playlist,
    SongQueue,
    Song,
    Album,
    Artists,
    ForwardRequest,
    PlaylistReturnType,
    RecommendationsReturnType,
    SearchReturnType,
    SongReturnType,
    CustomDataReturnType,
    PlaybackDetailsReturnType,
    PlaylistAndSongsReturnType,
    SongsWithPageTokenReturnType,
)


# https://stackoverflow.com/questions/38235997/how-to-implement-recvmsg-with-asyncio
def _sock_recvmsg(loop, fut, registered, sock, bufsize, ancbufsize):
    self = loop
    fd = sock.fileno()
    if registered:
        self.remove_reader(fd)
    if fut.cancelled():
        return
    try:
        data = sock.recvmsg(bufsize, ancbufsize)
    except (BlockingIOError, InterruptedError):
        self.add_reader(fd, self._sock_recvmsg, fut, True, sock, bufsize, ancbufsize)
    except Exception as exc:
        fut.set_exception(exc)
    else:
        fut.set_result(data)


def sock_recvmsg(loop, sock, bufsize, ancbufsize=0):
    self = loop
    if sock.gettimeout() != 0:
        raise ValueError("the socket must be non-blocking")
    fut = asyncio.futures.Future(loop=self)
    self._sock_recvmsg(fut, False, sock, bufsize, ancbufsize)
    return fut


asyncio.unix_events._UnixSelectorEventLoop._sock_recvmsg = _sock_recvmsg
asyncio.unix_events._UnixSelectorEventLoop.sock_recvmsg = sock_recvmsg

loop = asyncio.get_event_loop()


def generate_event_reply(request, data):
    return {
        "type": "REPLY",
        "data": {"id": request["id"], "event": request["event"], "args": data},
    }


class ExtensionEventHandler:
    def __init__(self) -> None:
        self.callbacks = {}

    async def add_listener(self, event_name, callback, callback_hints):
        if event_name not in self.callbacks:
            self.callbacks[event_name] = []
        self.callbacks[event_name].append({
            "handler": callback,
            "hints": callback_hints
        })

        data = generate_event_request("registerListener", [event_name])
        await loop.sock_sendall(
            client, json.dumps(data, cls=EnhancedJSONEncoder).encode() + b"\x0c"
        )

    async def on_oauth_callback(self, callback: Callable[[str], None]):
        return await self.add_listener("oauthCallback", callback, [])

    async def on_song_queue_changed(self, callback: Callable[[SongQueue], None]):
        return await self.add_listener("songQueueChanged", callback), [SongQueue]

    async def on_seeked(self, callback: Callable[[int], None]):
        return await self.add_listener("seeked", callback, [])

    async def on_volume_changed(self, callback: Callable[[int], None]):
        return await self.add_listener("volumeChanged", callback, [])

    async def on_player_state_changed(
        self,
        callback: Callable[[Literal["PLAYING", "PAUSED", "STOPPED", "LOADING"]], None],
    ):
        return await self.add_listener("playerStateChanged", callback, [])

    async def on_song_changed(self, callback: Callable[[Song], None]):
        return await self.add_listener("songChanged", callback, [Song])

    async def on_preference_changed(self, callback: Callable[[any], None]):
        return await self.add_listener("preferenceChanged", callback, [])

    async def on_song_added(self, callback: Callable[[list[Song]], None]):
        return await self.add_listener("songAdded", callback, [Song])

    async def on_song_removed(self, callback: Callable[[list[Song]], None]):
        return await self.add_listener("songRemoved", callback, [Song])

    async def on_playlist_added(self, callback: Callable[[list[Playlist]], None]):
        return await self.add_listener("playlistAdded", callback, [Playlist])

    async def on_playlist_removed(self, callback: Callable[[list[Playlist]], None]):
        return await self.add_listener("playlistRemoved", callback, [Playlist])

    async def requestedAlbumSongs(
        self,
        callback: Callable[
            [[Album, any]], SongsWithPageTokenReturnType | ForwardRequest
        ],
    ):
        return await self.add_listener("requestedAlbumSongs", callback, [Album, any])

    async def requestedArtistSongs(
        self,
        callback: Callable[
            [list[Artists, any]], SongsWithPageTokenReturnType | ForwardRequest
        ],
    ):
        return await self.add_listener("requestedArtistSongs", callback, [Artists, any])

    async def requestedLyrics(
        self, callback: Callable[[Song], str | ForwardRequest]
    ):
        return await self.add_listener("requestedLyrics", callback, [Song])

    async def requestedPlaylistFromURL(
        self,
        callback: Callable[
            [str, bool], PlaylistAndSongsReturnType | ForwardRequest
        ],
    ):
        return await self.add_listener("requestedPlaylistFromURL", callback, [])

    async def requestedPlaylistSongs(
        self,
        callback: Callable[
            [str, bool, any], SongsWithPageTokenReturnType | ForwardRequest
        ],
    ):
        return await self.add_listener("requestedPlaylistSongs", callback, [])

    async def requestedPlaylists(
        self, callback: Callable[[bool], PlaylistReturnType]
    ):
        return await self.add_listener("requestedPlaylists", callback, [])

    async def requestedRecommendations(
        self, callback: Callable[[], RecommendationsReturnType | ForwardRequest]
    ):
        return await self.add_listener("requestedRecommendations", callback, [])

    async def requestedSearchResult(
        self, callback: Callable[[str], SearchReturnType | ForwardRequest]
    ):
        return await self.add_listener("requestedSearchResult", callback, [])

    async def requestedSongFromURL(
        self, callback: Callable[[str, bool], SongReturnType | ForwardRequest]
    ):
        return await self.add_listener("requestedSongFromURL", callback, [])

    async def customRequest(
        self, callback: Callable[[str], CustomDataReturnType]
    ):
        return await self.add_listener("customRequest", callback, [])

    async def playbackDetailsRequested(
        self,
        callback: Callable[[Song], PlaybackDetailsReturnType | ForwardRequest],
    ):
        return await self.add_listener("playbackDetailsRequested", callback, [Song])
    
    def convert_args_to_hints(self, args, hints):
        conv = []
        if len(args) == len(hints):
            for i in range(len(hints)):
                if inspect.isclass(hints[i]):
                    
                    if isinstance(args[i], list):
                        instance = []
                        for a in args[i]:
                            instance.append(hints[i](**a))
                    else:
                        instance = hints[i](**args[i])
                    conv.append(instance)
                else:
                    conv.append(args[i])
                    
            return conv
        return args

    async def emit_event(self, request):
        event_name = request["event"]
        if event_name in self.callbacks:
            for callback_map in self.callbacks[event_name]:
                callback = callback_map["handler"]
                hints = callback_map["hints"]
                args = self.convert_args_to_hints(args=request["args"], hints=hints)
                
                callback_res = callback(*args)
                if inspect.iscoroutine(callback_res):
                    callback_res = await callback_res

                if callback_res is not None:
                    data = generate_event_reply(request, [callback_res])
                    await loop.sock_sendall(
                        client,
                        json.dumps(data, cls=EnhancedJSONEncoder).encode() + b"\x0c",
                    )


event_handler = ExtensionEventHandler()


async def read_pipe():
    half_read_data = b""
    while True:
        data_tmp = await loop.sock_recvmsg(client, 1024)

        split = data_tmp[0].split(b"\x0c")
        for i in range(len(split) - 1):
            split[i] = split[i] + b"\x0c"

        for s in split:
            if len(s) == 0:
                continue

            if not (s.endswith(b"\x0c")):
                half_read_data += s
                continue
            elif len(half_read_data) != 0:
                half_read_data += s
            else:
                half_read_data = s

            parsed = json.loads(half_read_data.strip())

            half_read_data = b""
            data = parsed["data"]
            if isinstance(data, str):
                data = json.loads(data)
                
            print("Got data", flush=True)

            if parsed["type"] == "REPLY":
                loop.create_task(api._resolve_future(data))

            elif parsed["type"] == "EVENT":
                loop.create_task(event_handler.emit_event(data))

            elif parsed["type"] == "CALLBACK":
                loop.create_task(api.trigger_callback(data["id"], data["args"]))


async def start():
    await read_pipe()

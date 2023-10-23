import asyncio
import inspect
import json
from moosyncLib.utils import generate_event_request, EnhancedJSONEncoder, client
from moosyncLib.data import Album, Artists, ContextMenuItem, EntitySearchOptions, Genre, Playlist, Song
from moosyncLib.data import SongSearchOptions
from typing import List
import uuid

future_map = {}
loop = asyncio.get_event_loop()

callback_map = {}

class ExtensionAPI:
    async def send(self, method, args):
        future = loop.create_future()
        data = generate_event_request(method, args)

        future_map[data["data"]["id"]] = future
        await loop.sock_sendall(
            client, json.dumps(data, cls=EnhancedJSONEncoder).encode() + b"\x0c"
        )
        res = await future
        return res
    
    class PlayerControls:
        def __init__(self, outer):
            self.outer = outer
            
        async def play(self):
            return await self.outer.send("player.play", [])
            
        async def pause(self):
            return await self.outer.send("player.pause", [])
            
        async def stop(self):
            return await self.outer.send("player.stop", [])
            
        async def next_song(self):
            return await self.outer.send("player.nextSong", [])
            
        async def prev_song(self):
            return await self.outer.send("player.prevSong", [])

    @property       
    def player(self):
        return self.PlayerControls(self)

    async def get_current_cong(self) -> Song:
        res = await self.send("getCurrentSong", [])
        return res

    async def get_songs(self, song_options: SongSearchOptions) -> list[Song]:
        return await self.send("getSongs", [song_options])

    async def get_entity(
        self, entity_options: EntitySearchOptions
    ) -> list[Artists | Album | Genre | Playlist]:
        return await self.send("getEntity", [entity_options])

    async def get_volume(self) -> int:
        return await self.send("getVolume", [])

    async def get_time(self) -> float:
        return await self.send("getTime", [])

    async def get_queue(self) -> list[Song]:
        return await self.send("getQueue", [])

    async def get_preferences(self, key: str, default_value: any) -> any:
        return await self.send("getPreferences", [key, default_value])

    async def set_preferences(self, key: str, value: any) -> None:
        return await self.send("setPreferences", [key, value])

    async def get_secure(self, key: str, default_value: str) -> str:
        return await self.send("getSecure", [key, default_value])

    async def set_secure(self, key: str, value: str) -> None:
        return await self.send("setSecure", [key, value])

    async def add_songs(self, songs: list[Song]) -> None:
        return await self.send("addSongs", [*songs])

    async def remove_song(self, song: Song) -> None:
        return await self.send("removeSong", [song])

    async def add_playlist(self, playlist: Playlist) -> str:
        return await self.send("addPlaylist", [playlist])

    async def add_songs_to_playlist(self, playlist_id: str, songs: list[Song]) -> None:
        return await self.send("addSongsToPlaylist", [playlist_id, *songs])

    async def register_OAuth(self, path: str) -> None:
        return await self.send("registerOAuth", [path])

    async def open_external_url(self, url: str) -> None:
        return await self.send("openExternalURL", [url])

    async def set_context_menu_item(self, items: List[ContextMenuItem]) -> None:
        for i in items:
            if i.handler is not None:
                id = str(uuid.uuid4())
                callback_map[id] = i.handler
                i.handler = id
        return await self.send("setContextMenuItem", [*items])

    async def remove_context_menu_item(self, index: int) -> None:
        return await self.send("removeContextMenuItem", [index])

    async def get_context_menu_items(self) -> List[ContextMenuItem]:
        return await self.send("getContextMenuItems", [])

    async def change_account_auth_status(
        self, id: str, logged_in: bool, username: str
    ) -> None:
        return await self.send("changeAccountAuthStatus", [id, logged_in, username])

    async def open_login_modal(self, options) -> bool:
        return await self.send("openLoginModal", [options])

    async def close_login_modal(self) -> None:
        return await self.send("closeLoginModal", [])

    async def show_toast(self, message: str, duration: int, type: str) -> None:
        return await self.send("showToast", [message, duration, type])

    async def set_artist_editable_info(self, artist_id: str, object: dict) -> None:
        return await self.send("setArtistEditableInfo", [artist_id, object])

    async def set_album_editable_info(self, album_id: str, object: dict) -> None:
        return await self.send("setAlbumEditableInfo", [album_id, object])

    async def get_installed_extensions(self) -> list[str]:
        return await self.send("getInstalledExtensions", [])

    async def _resolve_future(self, request):
        id = request["id"]
        if id in future_map:
            future = future_map[id]
            del future_map[id]

            result = None
            args = request["args"]
            if args is not None and len(request["args"]) > 0:
                result = request["args"][0]
            future.set_result(result)
            
    async def trigger_callback(self, id: str, args):
        if id in callback_map:
            callback = callback_map[id]
            callback_res = callback(*args)
            if inspect.iscoroutine(callback_res):
                callback_res = await callback_res

api = ExtensionAPI()

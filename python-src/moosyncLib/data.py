from dataclasses import dataclass
from typing import Callable, Dict, Literal, Optional, List


@dataclass
class Genre:
    genre_id: str
    genre_name: str
    genre_song_count: Optional[int] = None


@dataclass
class SearchableGenre:
    genre_id: Optional[str] = None
    genre_name: Optional[str] = None
    genre_song_count: Optional[int] = None


@dataclass
class Album:
    album_id: str
    album_name: str
    album_coverPath_high: Optional[str] = None
    album_coverPath_low: Optional[str] = None
    album_song_count: Optional[int] = None
    album_artist: Optional[str] = None
    album_extra_info: Optional[dict] = None
    year: Optional[int] = None


@dataclass
class SearchableAlbum:
    album_id: Optional[str] = None
    album_name: Optional[str] = None
    album_coverPath_high: Optional[str] = None
    album_coverPath_low: Optional[str] = None
    album_song_count: Optional[int] = None
    album_artist: Optional[str] = None
    album_extra_info: Optional[dict] = None
    year: Optional[int] = None


@dataclass
class Artists:
    artist_id: str
    artist_name: str
    artist_mbid: Optional[str] = None
    artist_coverPath: Optional[str] = None
    artist_song_count: Optional[int] = None
    artist_extra_info: Optional[dict] = None


@dataclass
class SearchableArtists:
    artist_id: Optional[str] = None
    artist_name: Optional[str] = None
    artist_mbid: Optional[str] = None
    artist_coverPath: Optional[str] = None
    artist_song_count: Optional[int] = None
    artist_extra_info: Optional[dict] = None


@dataclass
class Playlist:
    playlist_id: str
    playlist_name: str
    playlist_desc: Optional[str] = None
    playlist_coverPath: Optional[str] = None
    playlist_path: Optional[str] = None
    icon: Optional[str] = None
    extension: Optional[str] = None


@dataclass
class SearchablePlaylist:
    playlist_id: Optional[str] = None
    playlist_name: Optional[str] = None
    playlist_desc: Optional[str] = None
    playlist_coverPath: Optional[str] = None
    playlist_path: Optional[str] = None
    icon: Optional[str] = None
    extension: Optional[str] = None


@dataclass
class Song:
    _id: str
    title: str
    date_added: int
    type: Literal["LOCAL", "YOUTUBE", "SPOTIFY", "URL", "DASH", "HLS"]
    duration: float

    path: Optional[str] = None
    size: Optional[int] = None
    song_coverPath_low: Optional[str] = None
    song_coverPath_high: Optional[str] = None
    album: Optional[Album] = None
    artists: Optional[list[Artists]] = None
    date: Optional[str] = None
    year: Optional[int] = None
    genre: list[str] = None
    lyrics: Optional[str] = None
    releaseType: Optional[list[str]] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    container: Optional[str] = None
    sampleRate: Optional[int] = None
    hash: Optional[str] = None
    url: Optional[str] = None
    playbackUrl: Optional[str] = None
    icon: Optional[str] = None
    playCount: Optional[int] = None
    showInLibrary: Optional[bool] = None


@dataclass
class SearchableSong:
    _id: Optional[str] = None
    title: Optional[str] = None
    type: Optional[Literal["LOCAL", "YOUTUBE", "SPOTIFY", "URL", "DASH", "HLS"]] = None
    url: Optional[str] = None
    extension: Optional[str] = None
    hash: Optional[str] = None
    showInLibrary: Optional[bool] = None
    path: Optional[str] = None
    playbackUrl: Optional[str] = None


@dataclass
class EntitySearchOptions:
    artist: Optional[SearchableArtists] | bool = None
    album: Optional[SearchableAlbum] | bool = None
    artist: Optional[SearchableArtists] | bool = None
    playlist: Optional[SearchablePlaylist] | bool = None
    genre: Optional[SearchableGenre] | bool = None
    inclusive: Optional[bool] = None
    invert: Optional[bool] = None


@dataclass
class SongQueue:
    data: Dict[str, Song]
    order: list[Dict[str, str]]
    index: int


@dataclass
class SongSortOptions:
    type: Literal[
        "_id",
        "title",
        "type",
        "url",
        "extension",
        "hash",
        "showInLibrary",
        "path",
        "playbackUrl",
        "size",
        "duration",
        "date",
        "year",
        "playCount",
    ]
    asc: bool


@dataclass
class SongSearchOptions:
    song: Optional[SearchableSong] = None
    album: Optional[SearchableAlbum] = None
    artist: Optional[SearchableArtists] = None
    playlist: Optional[SearchablePlaylist] = None
    genre: Optional[SearchableGenre] = None
    sortBy: Optional[SongSortOptions] = None
    inclusive: bool = False
    invert: bool = False


@dataclass
class ForwardRequest:
    forwardTo: Literal["youtube", "spotify"] | str
    transformedData: any


@dataclass
class PlaylistReturnType:
    playlists: list[Playlist]


@dataclass
class SongReturnType:
    songs: list[Song]


@dataclass
class SearchReturnType:
    songs: list[Song]
    playlists: list[Playlist]
    artists: list[Artists]
    albums: list[Album]


@dataclass
class PlaybackDetailsReturnType:
    duration: int
    url: str


@dataclass
class CustomDataReturnType:
    mimeType: Optional[str] = None
    data: Optional[bytes] = None
    redirectUrl: Optional[str] = None


@dataclass
class SongReturnType:
    song: Song


@dataclass
class PlaylistAndSongsReturnType:
    playlist: Playlist
    songs: list[Song]


@dataclass
class RecommendationsReturnType:
    songs: list[Song]


@dataclass
class SongsWithPageTokenReturnType:
    songs: list[Song]
    nextPageToken: any


@dataclass
class ContextMenuItem:
    type: Literal[
        "SONGS",
        "GENERAL_SONGS",
        "PLAYLIST",
        "GENERAL_PLAYLIST",
        "PLAYLIST_CONTENT",
        "QUEUE_ITEM",
        "ARTIST",
        "ALBUM",
    ]
    label: str
    disabled: Optional[bool] = False
    children: Optional[List["ContextMenuItem"]] = None
    handler: Optional[Callable[[List[Song] | Playlist | Song | Artists | Album | None], None]] = None

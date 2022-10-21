import { MoosyncExtensionTemplate, Playlist, PlayerState, Song, SongQueue, Artists } from '@moosync/moosync-types'
import { resolve } from 'path'

const sampleSong: Song = {
  _id: 'Another random ID',
  title: 'Example song',
  duration: 0,
  date_added: Date.now(),
  type: 'URL',
  playbackUrl:
    'https://file-examples.com/storage/fe8788b10b62489539afcfd/2017/11/file_example_MP3_5MG.mp3' /* If the URL is directly playable, duration is fetched at runtime */
}

const samplePlaylist: Playlist = {
  playlist_id: 'Some random generated ID',
  playlist_name: 'Hello this is a playlist',
  playlist_song_count: 69,
  playlist_coverPath: 'https://avatars.githubusercontent.com/u/91860733?s=200&v=4',
  icon: resolve(__dirname, '../assets/icon.svg')
}

const sampleArtist: Artists = {
  artist_id: 'random generated ID',
  artist_name: 'My Artist',
  artist_coverPath: 'https://avatars.githubusercontent.com/u/91860733?s=200&v=4'
}
export class MyExtension implements MoosyncExtensionTemplate {
  private interval: ReturnType<typeof setInterval> | undefined

  async onStarted() {
    console.info('Extension started')
    this.registerEvents()

    this.interval = setInterval(() => {
      this.setProgressbarWidth()
    }, 1000)

    api.setContextMenuItem({
      type: 'SONGS',
      label: 'Test context menu item',
      handler: (songs) => {
        console.info('Clicked context menu item with data', songs)
      }
    })
  }

  private async onSongChanged(song: Song) {
    console.debug(song)
  }

  private async onPlayerStateChanged(state: PlayerState) {
    console.debug(state)
  }

  private async onSongQueueChanged(queue: SongQueue) {
    console.debug(queue.index)
  }

  private async onVolumeChanged(volume: number) {
    console.debug(volume)
  }

  async onStopped() {
    // Cleanup intervals, timeout, etc in onStopped
    if (this.interval) {
      clearInterval(this.interval)
    }

    console.info('Extension stopped')
  }

  private async onPreferenceChanged({ key, value }: { key: string; value: any }): Promise<void> {
    console.info('Preferences changed at', key, 'with value', value)
  }

  async setProgressbarWidth() {
    await api.setPreferences('test_progressBar', Math.random() * 100 + 1)
  }

  private async registerEvents() {
    api.on('requestedPlaylists', async () => {
      return {
        playlists: [samplePlaylist]
      }
    })

    api.on('requestedPlaylistSongs', async () => {
      return {
        songs: [sampleSong]
      }
    })

    api.on('requestedLyrics', async (song) => {
      return 'Lorem Ipsum'
    })

    api.on('requestedSearchResult', async (term) => {
      return {
        songs: [sampleSong],
        playlists: [samplePlaylist],
        artists: [sampleArtist],
        albums: []
      }
    })

    api.on('playerStateChanged', this.onPlayerStateChanged.bind(this))
    api.on('preferenceChanged', this.onPreferenceChanged.bind(this))
    api.on('volumeChanged', this.onVolumeChanged.bind(this))
    api.on('songChanged', this.onSongChanged.bind(this))
    api.on('songQueueChanged', this.onSongQueueChanged.bind(this))
    api.on('seeked', async (time) => console.debug('Player seeked to', time))

    await api.registerOAuth('exampleOAuth') /* Callback paths are case-insensitive */

    api.on('oauthCallback', async (url) => {
      console.info('OAuth callback triggered', url)
    })
  }
}

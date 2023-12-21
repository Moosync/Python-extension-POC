import { ExtensionContextMenuItem, ExtraExtensionEventTypes, MoosyncExtensionTemplate, extensionAPI } from '@moosync/moosync-types'
import { Socket, createServer } from 'net'
import { access, chmod, mkdir, rm } from 'fs/promises'

import { EventEmitter } from 'events'
import bufferSplit from 'buffer-split'
import path from 'path'
import { spawn } from 'child_process'
import { v4 } from 'uuid'

type Message = { id: string; event: keyof MoosyncExtensionTemplate | ExtraExtensionEventTypes | keyof extensionAPI; args: unknown[] }
type MessageType = 'EVENT' | 'REPLY' | "REQUEST" | 'CALLBACK'
const pipePath = path.join(__dirname, 'pipes', 'ipc.sock')

export class MyExtension implements MoosyncExtensionTemplate {
  private socket?: Socket
  private socketWriteQueue: [MessageType, Message][] = []
  private pythonReceiver = new EventEmitter()
  private child: ReturnType<typeof spawn> | undefined

  private async createPipes() {
    try {
      await access(path.dirname(pipePath))
      await rm(pipePath, { force: true })
    } catch {
      await mkdir(path.dirname(pipePath))
    }

    const server = createServer().listen(pipePath)
    server.on('connection', (socket) => {
      this.socket = socket
      this.readFromPython()
      this.emptyWriteQueue()
    })
  }

  private handleData(type: MessageType, data: Message) {
    if (type === "REPLY") {
      this.pythonReceiver.emit(data.id, data)
      return
    }

    if (type === "REQUEST") {
      if ((data.event as string) === "registerListener") {
        this.registerEvent(data.args?.[0] as ExtraExtensionEventTypes)
        return
      }

      this.handlePythonRequests(data.event as keyof extensionAPI, data.args).then((...args: unknown[]) => {
        this.send('REPLY', {
          id: data.id,
          event: data.event,
          args: args
        })
      })
    }
  }

  private async handlePythonRequests(method: keyof extensionAPI, args: unknown[]) {
    const validMethods: (keyof extensionAPI)[] = [
      'addPlaylist',
      'addSongs',
      'updateSong',
      'addSongsToPlaylist',
      'changeAccountAuthStatus',
      'closeLoginModal',
      'getContextMenuItems',
      'getCurrentSong',
      'getEntity',
      'getInstalledExtensions',
      'getPlayerState',
      'getPreferences',
      'getQueue',
      'getSecure',
      'getSongs',
      'getTime',
      'getVolume',
      'openExternalURL',
      'openLoginModal',
      'registerAccount',
      'registerOAuth',
      'removeContextMenuItem',
      'removeSong',
      'setAlbumEditableInfo',
      'setArtistEditableInfo',
      'setContextMenuItem',
      'setPreferences',
      'setSecure',
      'showToast',
      'addUserPreference',
      'removeUserPreference'
    ]

    if (method === 'setContextMenuItem') {
      for (const a of (args as ExtensionContextMenuItem<'GENERAL_SONGS'>[])) {
        const id = a.handler as unknown as string

        a.handler = (...args: unknown[]) => {
          this.send('CALLBACK', {
            id,
            event: 'setContextMenuItem',
            args
          })
        }
      }
    }

    if (method === 'registerAccount') {
      const signInId = args[3] as string
      const signOutId = args[4] as string

        ; (args as Parameters<extensionAPI['registerAccount']>)[3] = (...args: unknown[]) => {
          this.send('CALLBACK', {
            id: signInId,
            event: 'registerAccount',
            args
          })
        }

        ; (args as Parameters<extensionAPI['registerAccount']>)[4] = (...args: unknown[]) => {
          this.send('CALLBACK', {
            id: signOutId,
            event: 'registerAccount',
            args
          })
        }
    }

    if (method.startsWith('player')) {
      const innerMethod = method.slice(7) as keyof extensionAPI['player']

      const validInnerMethods: (keyof extensionAPI['player'])[] = [
        'nextSong',
        'pause',
        'play',
        'prevSong', ,
        'stop'
      ]

      if (validInnerMethods.includes(innerMethod)) {
        const result = await ((api.player[innerMethod] as Function)(...args))
        return result
      }
    }

    if (validMethods.includes(method)) {
      console.log(method)
      const result = await (api[method] as Function)(...args)
      return result
    }
  }

  private readFromPython() {
    if (this.socket) {
      let halfReadData = Buffer.alloc(0)
      this.socket.on('data', (data) => {
        const split = bufferSplit(data, Buffer.from([12]), true)
        for (const s of split) {
          if (s[s.length - 1] !== 12) {
            halfReadData = Buffer.concat([halfReadData, s])
            return
          } else if (halfReadData.length != 0) {
            halfReadData = Buffer.concat([halfReadData, s])
          } else {
            halfReadData = s
          }

          const parsed = JSON.parse(halfReadData.toString().trim())
          this.handleData(parsed["type"], parsed["data"])
          halfReadData = Buffer.alloc(0)
        }

      })
    }
  }

  private emptyWriteQueue() {
    for (const m of this.socketWriteQueue) {
      this.writeToPython(m[0], m[1])
    }

    this.socketWriteQueue = []
  }

  private writeToPython(type: MessageType, message: Message) {
    if (this.socket) {
      const data = { type, data: message }
      console.log('writing to socket')
      this.socket.write(JSON.stringify(data) + "\x0c")
    } else {
      this.socketWriteQueue.push([type, message])
    }
  }

  private async sendAsync<T>(type: MessageType, message: Message): Promise<T> {
    const promise = new Promise<T>((resolve) => {
      this.pythonReceiver.once(message.id, (data: Message) => {
        console.log('resolving', data.args)
        resolve(data?.args?.[0] as T)
      })
    })

    this.writeToPython(type, message)
    return promise
  }

  private send(type: MessageType, message: Message) {
    this.writeToPython(type, message)
  }

  async onStopped(): Promise<void> {
    this.child?.kill()
  }

  async onStarted() {
    console.log('spawning child')
    const pythonBin = path.join(__dirname, 'python-bin.pex')
    await chmod(pythonBin, 0o755)

    await this.createPipes()

    this.send('EVENT', { event: 'onStarted', args: [], id: v4() })

    this.child = spawn(pythonBin, [__dirname, pipePath], {
      stdio: 'pipe'
    })

    this.child?.on('disconnect', () => {
      console.error("Child disconnected")
    })

    this.child?.on('exit', (err) => {
      console.error('child exited', err)
    })

    this.child?.on('error', function (err) {
      console.error('Failed to start child.', err)
    })
    this.child?.on('close', function (code) {
      console.error('Child process exited with code ' + code)
    })

    this.child?.stdout.on('data', (buf: Buffer) => console.log('from python:', buf.toString()))
    this.child?.stderr.on('data', (buf: Buffer) => console.error('from python:', buf.toString()))

    console.log('spawned child')
  }

  private registerEvent(eventName: ExtraExtensionEventTypes) {
    const voidEvents: ExtraExtensionEventTypes[] = [
      'oauthCallback',
      'songQueueChanged',
      'seeked',
      'volumeChanged',
      'playerStateChanged',
      'songChanged',
      'preferenceChanged',
      'songAdded',
      'songRemoved',
      'playlistAdded',
      'playlistRemoved',
      'songQueueChanged',
    ]

    const replyEvents: ExtraExtensionEventTypes[] = [
      'requestedAlbumSongs',
      'requestedArtistSongs',
      'requestedLyrics',
      'requestedPlaylistFromURL',
      'requestedPlaylistSongs',
      'requestedPlaylists',
      'requestedRecommendations',
      'requestedSearchResult',
      'requestedSongFromURL',
      'customRequest',
      'playbackDetailsRequested'
    ]

    if (voidEvents.includes(eventName)) {
      api.on(eventName as any, async (...args: unknown[]) => this.send('EVENT', { event: eventName, args, id: v4() }))
      return
    }

    if (replyEvents.includes(eventName)) {
      api.on(eventName as any, (...args: unknown[]) => this.sendAsync('EVENT', { event: eventName, args, id: v4() }))
      return
    }
  }
}
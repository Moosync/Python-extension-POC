import { ExtraExtensionEventTypes, MoosyncExtensionTemplate } from '@moosync/moosync-types'
import { access, chmod, mkdir, rm } from 'fs/promises'

import ipc from 'node-ipc'
import path from 'path'
import { spawn } from 'child_process'
import { v4 } from 'uuid'

type Message = { id: string; event: keyof MoosyncExtensionTemplate | ExtraExtensionEventTypes; args: unknown[] }
type MessageType = 'EVENT' | 'REPLY'
const pipePath = path.join(__dirname, 'pipes', 'ipc.sock')

ipc.config.logger = () => {}

function generateHugeData() {
  const data = {}
  for (let i = 0; i <= 65535; i++) {
    data[i] = v4()
  }

  return data
}

export class MyExtension implements MoosyncExtensionTemplate {
  private socket?: unknown
  private socketWriteQueue: [MessageType, Message][] = []

  private async createPipes() {
    try {
      await access(path.dirname(pipePath))
      await rm(pipePath, { force: true })
    } catch {
      await mkdir(path.dirname(pipePath))
    }

    ipc.serve(pipePath, () => {
      ipc.server.on('connect', (socket) => {
        console.log('connected')
        this.socket = socket
        this.emptyWriteQueue()
      })

      ipc.server.on('data', (buf) => {
        console.log('got data', buf.toString())
      })
    })

    ipc.server.start()
  }

  private emptyWriteQueue() {
    for (const m of this.socketWriteQueue) {
      this.writeToPython(m[0], m[1])
    }

    this.socketWriteQueue = []
  }

  private writeToPython(type: MessageType, message: Message) {
    if (this.socket) {
      ipc.server.emit(this.socket, type, JSON.stringify(message))
    } else {
      this.socketWriteQueue.push([type, message])
    }
  }

  async onStarted() {
    const pythonBin = path.join(__dirname, 'python-bin.pex')
    await chmod(pythonBin, 0o755)

    await this.createPipes()

    this.writeToPython('EVENT', { event: 'onStarted', args: [generateHugeData()], id: v4() })

    const child = spawn(pythonBin, [__dirname, pipePath], {
      stdio: 'pipe'
    })

    child.on('error', function (err) {
      console.error('Failed to start child.', err)
    })
    child.on('close', function (code) {
      console.error('Child process exited with code ' + code)
    })

    child.stdout.on('data', (buf: Buffer) => console.log('from python:', buf.toString()))
    child.stderr.on('data', (buf: Buffer) => console.error('from python:', buf.toString()))

    // this.registerEvents()
  }

  private registerEvents() {
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
      'preferenceChanged'
    ]

    for (const e of voidEvents) {
      api.on(e as any, async (...args: unknown[]) =>
        this.writeToPython('EVENT', { event: e, args, id: v4() })
      )
    }
  }
}

new MyExtension().onStarted()